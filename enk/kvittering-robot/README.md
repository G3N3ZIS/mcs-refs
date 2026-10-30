# Kvitteringsrobot

Henter kvitteringer fra en Gmail-etikett og fra mappen `innboks/`. Hver kvittering blir arkivert som bilag i `bilag/ÅÅÅÅ/ÅÅÅÅ-MM-DD_leverandør.pdf` og ført som en rad i fanen **Utgifter** i `../ENK-regnskap-2027.xlsx`. Roboten leser dato, beløp og leverandør, og velger kategori ut fra reglene i `config.json`.

Alle rader merkes **«AUTO – kontroller»**. Etter bokføringsloven er det du som har ansvaret, så gå over de nye radene én gang i uka. Er beløpet i utenlandsk valuta (for eksempel USD), står cellen for beløp tom, og du fyller inn NOK-beløpet fra bankutskriften.

## Oppsett (én gang)

1. Installer Python 3.10 eller nyere fra python.org. Kryss av for «Add to PATH» på Windows.
2. Installer pakkene som trengs:
   ```
   pip install openpyxl pypdf
   ```
3. Kopier `config.example.json` til `config.json`.
4. **Gmail (valgfritt):**
   - Lag etiketten `Kvitteringer` i Gmail.
   - Lag et filter som gir den etiketten til e-post fra leverandørene dine, eller videresend kvitteringer til `dinadresse+kvittering@gmail.com` og filtrer på den adressen.
   - Lag et app-passord: Google-konto → Sikkerhet → Totrinnsbekreftelse → App-passord.
   - Lagre app-passordet som miljøvariabelen `ENK_GMAIL_APP_PASSORD`, ikke i filen:
     - Windows: `setx ENK_GMAIL_APP_PASSORD "xxxx xxxx xxxx xxxx"`
     - Mac/Linux: legg `export ENK_GMAIL_APP_PASSORD="..."` i `~/.zshrc`
   - Sett `"aktiv": true` og fyll inn adressen din i `config.json`.
5. **Kvitteringer fra mobilen:** ta bilde eller skann, og lagre i `innboks/`. Har du synk med OneDrive, Dropbox eller Google Drive, kan du peke `innboks` i `config.json` til en mappe der.

## Kjøring

```
python kvittering_robot.py --test   # viser hva som ville skjedd, endrer ingenting
python kvittering_robot.py          # gjør det
```

Excel må være lukket når roboten skriver til arket. Før hver skriving tas det en sikkerhetskopi av arket i `backup/`.

### Kjør automatisk hver dag

- **Windows:** Oppgaveplanlegging → Opprett enkel oppgave → Daglig.
  - Handling: `python`
  - Argument: `kvittering_robot.py`
  - Start i: denne mappen
- **Mac/Linux:** `crontab -e` og legg til:
  ```
  0 18 * * * cd /sti/til/kvittering-robot && python3 kvittering_robot.py >> robot.log 2>&1
  ```

## Lovkrav du selv må passe på

- Ta vare på bilagene i 5 år. Ha `bilag/` og `ENK-regnskap-2027.xlsx` i en sky-synket mappe, så du har en kopi utenfor PC-en.
- Ikke slett eller endre bilag i ettertid. Retter du noe i regnearket, skriver du hvorfor i kolonnen for merknad.
- Kvitteringer som bare er bilder, blir ikke lest av roboten. Den fører dato og fil, og du fyller inn beløp og kategori selv.
- Legg til nye leverandører i `regler` i `config.json`, så blir kategorien riktig neste gang.

`config.json`, `bilag/`, `innboks/`, `backup/` og `status.json` er utelatt fra git, så kvitteringer og passord havner aldri på GitHub.
