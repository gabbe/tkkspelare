# Hosting the player on voldemort (Apache, Debian 13)

The site is static files behind HTTP basic auth. Apache handles the shared
password and HTTPS; the app itself has no server-side code.

## One-time setup on the server

```bash
sudo apt install apache2 apache2-utils certbot python3-certbot-apache
sudo mkdir -p /var/www/tkkspelare
sudo chown $USER:www-data /var/www/tkkspelare       # the deploying user writes, Apache reads
sudo a2enmod headers deflate
sudo htpasswd -c /etc/apache2/tkkspelare.htpasswd kammarkoren
sudo cp spelare.thnkk.se.conf /etc/apache2/sites-available/
sudo a2ensite spelare.thnkk.se
sudo apachectl configtest && sudo systemctl reload apache2
```

DNS: an A record (and AAAA if the machine has IPv6) for `spelare.thnkk.se`
pointing at voldemort's public address, and ports 80 and 443 open to it.
Then:

```bash
sudo certbot --apache -d spelare.thnkk.se
```

certbot creates the `:443` site with the certificate and redirects `http`
to `https`. The password then never travels in the clear. Renewal is
automatic (systemd timer).

Adding or changing the shared login later:

```bash
sudo htpasswd /etc/apache2/tkkspelare.htpasswd kammarkoren
```

## Secret link without the password dialog

Some singers find the login dialog too hard. They get a link with a long
random token in the path instead, `https://spelare.thnkk.se/<token>/`, which
serves the same site without a login. The token is kept only on the server:

```bash
echo "Define TKK_SECRET $(openssl rand -hex 16)" | sudo tee /etc/apache2/tkkspelare-secret.conf
sudo cat /etc/apache2/tkkspelare-secret.conf        # the token to put in the link
```

certbot copied the `:80` site into `spelare.thnkk.se-le-ssl.conf` when it set up
HTTPS, so the `Include`, `Alias`, `RedirectMatch`, `<Location>` and
`Referrer-Policy` lines from `spelare.thnkk.se.conf` must be added there too
(the `Include` outside `<IfModule>`/`<VirtualHost>`, at the top of the file).
Then `sudo apachectl configtest && sudo systemctl reload apache2`.

To revoke the link (it has been forwarded outside the choir), write a new
token and reload. The normal login keeps working throughout.

Do not use `https://user:password@spelare.thnkk.se`: browsers refuse
`fetch()` from a page whose address contains credentials, so the song list
fails to load and only the test songs show.

## Deploying from the digitiser's machine

`deploy.py` in the repo root runs the Drive sync and copies the site to the
server over SSH in one go. It needs `ssh` on the path (Windows 10+ has it)
and these keys in `sync.local.json`:

```json
{"source": "G:/.../Digitala Noter/2. MuseScore",
 "musescore": "C:/Program Files/MuseScore 4/bin/MuseScore4.exe",
 "deploy_host": "voldemort",
 "deploy_dir": "/var/www/tkkspelare"}
```

Machine-specific keys can also sit under a `hosts` block keyed by host name,
see the README. `deploy_host` is whatever `ssh` accepts: a host alias from `~/.ssh/config`
(recommended, with a key, so no password prompt) or `user@voldemort.example`.

```bash
py deploy.py                 # sync Aktuellt from Drive, then upload
py deploy.py --all           # sync everything under "2. MuseScore"
py deploy.py --no-sync       # upload what is already in noter/ and library.json
```

What goes up: `index.html`, `robots.txt`, `vendor/`, `img/`, `noter/`, `library.json`
and `test/`. Nothing else from the repo. Files removed from Drive are removed
from the server as well, since the upload replaces the whole site directory
atomically (uploaded next to it, then swapped). The app icons live in `img/`,
not `icons/`: Debian's Apache aliases `/icons/` to its own directory listing icons.

## Checks after the first deploy

- `https://spelare.thnkk.se/` asks for the login once, then shows the player.
- Pick a song, press play: the browser must fetch `vendor/alphaTab.js` a second
  time for the audio worker and `vendor/soundfont/sonivox.sf3`; both are behind
  the same login and the browser reuses the credentials.
- `curl -I https://spelare.thnkk.se/library.json` without credentials must
  return `401`.

## Logs and weekly usage statistics

The site logs to `/var/log/apache2/spelare/` (`access.log`, `error.log`), outside
the `*.log` glob of Debian's Apache logrotate, so it can have its own retention:
90 days of raw logs (they hold IP addresses), see `logrotate-tkkspelare`.
Before 2026-11-05 the logs were `/var/log/apache2/spelare-*.log` (14 days).

Every Monday at 06:00 `weekly_stats.py` summarises the previous week (Mon–Sun)
into `/var/lib/tkkspelare-stats/<year>-W<week>.txt` and `.json`, and rebuilds
`total.txt` over all saved weeks. The summaries hold counts only (visitors, opened
songs per song, days, hours, devices, password vs. secret link), no IP addresses,
and are kept indefinitely. "Opened" means the song's `.mxl` was fetched; playback
happens in the browser and is not logged. Visitors are IP + browser, so one singer
on phone and computer counts twice.

Setup (done 2026-11-05):

```sh
sudo install -d -o root -g adm -m 750 /var/log/apache2/spelare
sudo cp deploy/logrotate-tkkspelare /etc/logrotate.d/tkkspelare
sudo install -D -m 755 deploy/weekly_stats.py /usr/local/lib/tkkspelare/weekly_stats.py
sudo cp deploy/tkkspelare-stats.service deploy/tkkspelare-stats.timer /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now tkkspelare-stats.timer
# point ErrorLog/CustomLog of both vhosts (:80 and -le-ssl) at spelare/, then
sudo apache2ctl configtest && sudo systemctl reload apache2
```

Reading: `ssh root@voldemort cat /var/lib/tkkspelare-stats/total.txt` (or a
week's `.txt`). Re-run a week with `weekly_stats.py --week 2026-W45`, or all
weeks still in the logs with `--backfill`. After changing the script, install
it again with the `install` line above.
