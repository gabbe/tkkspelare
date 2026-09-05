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

`deploy_host` is whatever `ssh` accepts: a host alias from `~/.ssh/config`
(recommended, with a key, so no password prompt) or `user@voldemort.example`.

```bash
py deploy.py                 # sync Aktuellt from Drive, then upload
py deploy.py --all           # sync everything under "2. MuseScore"
py deploy.py --no-sync       # upload what is already in noter/ and library.json
```

What goes up: `index.html`, `robots.txt`, `vendor/`, `noter/`, `library.json`
and `test/`. Nothing else from the repo. Files removed from Drive are removed
from the server as well, since the upload replaces the whole site directory
atomically (uploaded next to it, then swapped).

## Checks after the first deploy

- `https://spelare.thnkk.se/` asks for the login once, then shows the player.
- Pick a song, press play: the browser must fetch `vendor/alphaTab.js` a second
  time for the audio worker and `vendor/soundfont/sonivox.sf3`; both are behind
  the same login and the browser reuses the credentials.
- `curl -I https://spelare.thnkk.se/library.json` without credentials must
  return `401`.
