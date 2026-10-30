# ENK-robot for Google Sheets

Et Google Apps Script som hører til regnearket og kjører på Googles servere, så PC-en trenger ikke være på. Det gjør dette hver time:

1. Henter kvitteringer fra Gmail-etiketten **Kvitteringer** (vedlegg, eller selve e-posten lagret som PDF) og fra Drive-mappen **ENK/Innboks**. Ferdige e-poster flyttes til etiketten **Kvitteringer/Ført**.
2. Leser teksten med Googles egen tekstgjenkjenning (OCR). Det virker også på bilder og skannede kvitteringer.
3. Arkiverer kvitteringen som `ENK/Bilag/ÅÅÅÅ/ÅÅÅÅ-MM-DD_leverandør.pdf`.
4. Fører en rad i **Utgifter** med dato, leverandør, beløp, kategori og en klikkbar lenke til bilaget. Raden merkes **«AUTO – kontroller»**.

## Mappestruktur i Drive

```
ENK/
├── ENK-regnskap-2027      ← Google-arket (legg det her)
├── Bilag/2027/            ← roboten arkiverer hit
├── Innboks/               ← legg skann/bilder her
└── Dokumenter/
    ├── 01 Registrering (Brønnøysund, Altinn)
    ├── 02 NAV og AAP
    ├── 03 Skatt (skattekort, skattemelding)
    ├── 04 Kontrakter og utgående fakturaer
    ├── 05 Forretningsplan og budsjett
    └── 06 Bank og forsikring
```

Roboten finner `Bilag/` og `Innboks/` i den mappen regnearket ligger i. Arket må derfor ligge direkte i `ENK/`.

## Oppsett (ca. 10 minutter, én gang)

1. **Arket:** Last opp `ENK-regnskap-2027.xlsx` til `ENK/` i Drive. Åpne det og velg Fil → *Lagre som Google Regneark*. Slett .xlsx-filen etterpå.
2. **Scriptet:** I Google-arket velger du Utvidelser → *Apps Script*. Slett innholdet i `Kode.gs`, lim inn innholdet fra [`Kode.gs`](Kode.gs) og lagre.
3. **OCR:** I Apps Script klikker du **+** ved *Tjenester*, velger **Drive API** og trykker *Legg til*.
4. **Første kjøring:** Last arket på nytt. Velg menyen **ENK-robot** → *Hent kvitteringer nå*. Google ber deg godkjenne tilgang. Fordi det er ditt eget script, viser Google «ikke bekreftet app»: velg *Avansert* → *Gå til …*.
5. **Automatikk:** Velg **ENK-robot** → *Slå på automatisk kjøring (hver time)*.
6. **Gmail:** Lag etiketten `Kvitteringer`. Lag et filter som setter den på e-post fra leverandørene dine, eller videresend kvitteringer til `dinadresse+kvittering@gmail.com` og filtrer på den adressen.
7. **Mobil:** I Google Drive-appen trykker du **+** → *Skann* og lagrer i `ENK/Innboks`.

Kategoriene styres av fanen **Robot-regler**, som lages første gang roboten kjører. Legg til leverandører der. Fanen **Robot-logg** viser hva som har skjedd.

## Lovkrav du selv må passe på

- Gå over radene merket «AUTO» én gang i uka. Det er du som er ansvarlig for bokføringen.
- Bilag i utenlandsk valuta: fyll inn NOK-beløpet fra bankutskriften. Roboten lar beløpet stå tomt og skriver valutabeløpet i merknaden.
- Ikke slett eller endre noe i `Bilag/`. Alt skal tas vare på i 5 år.
- Slå på versjonslogg i arket (den er på som standard i Google Sheets). Den viser hvem som endret hva.
