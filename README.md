# Körspelare

Webbaserad övningsspelare för körsångare. Visar noterna, spelar upp dem och
låter var och en lyfta fram sin egen stämma. Byggd på [alphaTab](https://alphatab.net)
och MusicXML exporterad från MuseScore Studio.

Bakgrunden är en amatörkör som digitaliserar sina noter i MuseScore, dels för
att göra punktskrift (.brf) till en blind sångare, dels för att alla ska kunna
öva hemma utan att installera MuseScore.

## Vad spelaren kan

- Följa noterna under uppspelning, klicka på en takt för att hoppa dit
- Solo, tyst och volym per stämma, samt "dämpa övriga" för att höra sin egen
  stämma tydligt med de andra i bakgrunden
- Panorera en stämma till ena högtalaren och resten till den andra
- Tempo 40–200 procent
- Loopa ett markerat område, med repriser och hopp avstängda så att markeringen
  loopar exakt de takterna
- Byta instrument för alla stämmor (piano, kör, orgel, stråkar ...)
- Repriser och D.C./D.S. al Coda spelas i rätt ordning

## Kom igång

Sidan är statisk, men alphaTab kör i web workers och måste serveras över http:

```bash
py patch_alphatab.py          # hämtar alphaTab 1.8.4 och skriver vendor/alphaTab.js
py -m http.server 8765
```

Öppna http://127.0.0.1:8765/ . Utan eget notbibliotek visas testfixturen
`test/fixture.mxl`, en egenkomponerad SATB-snutt med repris, To Coda, D.C. al
Coda, basdivisi och en bindning över taktstreck.

Eget bibliotek: lägg `.mxl`-filer i `noter/` och skapa `library.json`:

```json
[
  {"title": "Rättnu min tid", "file": "noter/rattnu.mxl"},
  {"title": "Stjärntändningen", "file": "noter/stjarn.mxl"}
]
```

Båda ignoreras av git. Noter ligger aldrig i repot.

## prepare.py – gör MuseScore-exporten spelbar per stämma

alphaTab mixar per part, inte per stämma inom en part. Körnoter skrivs ofta som
S/A på ett system och T/B på ett annat. `prepare.py` skriver om exporten utan
att röra MuseScore-filen. Standardbiblioteket räcker, ingen venv.

```bash
py prepare.py in.mxl out.mxl --names "S/A=Sopran,Alt;T/B=Tenor,Bas" --explode "Bas=Bas 1,Bas 2" --copy-lyrics
```

1. Parts med flera stämmor delas i en part per stämma. `--names` namnger dem.
2. `--explode` delar divisi som är skrivet som ackord (Bas 1 och Bas 2 på samma
   skaft) i en part per ackordton, översta tonen först. Unisont går till båda.
3. `--copy-lyrics` ger en stämma utan text samma text som stämman som bär
   texten, ton för ton där de börjar samtidigt.
4. Bundna toner som fortsätter in i ny takt får explicit förtecken från
   bindningens början. alphaTab stavar annars efter tonarten, så ett fiss bundet
   över taktstreck i en tonart med b-förtecken ritas som gess i takt två.
   alphaTab döljer det överflödiga tecknet på bundna toner.
5. Hopp (D.C., D.S., To Coda, Coda, Fine, Segno) som MuseScore skriver som
   `<sound>` inuti `<direction>` kopieras till taktnivå, som är det enda stället
   alphaTab läser dem. Spelaren gör sedan "D.C." plus "To Coda" till "D.C. al
   Coda" (`fixJumps` i index.html).

Punkt 3 är en gissning per ton: där stämmorna har olika rytm får en ton utan
samtidig start i grannstämman ingen text. Kontrollera per sång.

## patch_alphatab.py – repriser före hopp

alphaTab 1.8.4 utför D.C./D.S. första gången den når takten, även när takten
också avslutar en repris som inte spelats färdigt. Rätt är repris först, sedan
hopp. Skriptet hämtar exakt version från CDN och lägger in kontrollen i
`MidiPlaybackController`. Det avbryter om ankartexten inte hittas exakt en gång,
alltså när en ny alphaTab-version ändrat koden. Tas bort när felet är rättat
uppströms. Efter hoppet spelas repriser inte om, som i MuseScore.

## Kända alphaTab-egenheter (1.8.4)

Dokumenterade här för att inte upptäckas igen. Alla har en lösning i koden.

- Hopp går före repris i samma takt. Se patch_alphatab.py.
- `<sound>` inuti `<direction>` läses bara för tempo. Se prepare.py punkt 5.
- Toner stavas efter tonart, inte efter MusicXML:s step och alter. Se punkt 4.
- Instrumentbyte: importen lagrar filens instrument som en beat-automation som
  skriver över `playbackInfo.program`. Båda måste ändras.
- `playbackInfo.volume` används både som MIDI-kanalvolym vid generering och som
  mixervolym som alphaTab lägger på igen i `readyForPlayback` efter varje
  MIDI-laddning, efter `midiLoaded`. Spelaren genererar med full kanalvolym och
  sätter sedan fältet till mixernivån.
- Ett uppspelningsområde lagras i ticks, som flyttar sig när repriser slås av
  eller på. Spelaren minns området som takt plus offset och mappar om.
- `api.midiLoaded.on(...)` registrerat efter första laddningen kraschar med
  oändlig rekursion i `loadedMidiInfo` (skrivfel i worker-proxyn). Registrera
  före första laddningen.

## Planerat

- Bibliotek som speglar körens Google Drive, med "Aktuellt" som startvy
- Bokmärken i en sång
- Rapportera fel i en takt till dem som digitaliserar
- Instrument-presets och val av soundfont
- Lösenordsskydd framför sidan

## Licens

MIT, se LICENSE. alphaTab är MPL 2.0 och ingår inte i repot.
