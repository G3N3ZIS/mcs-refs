/**
 * Kvitteringsrobot for ENK – Google Apps Script, bundet til regnearket.
 *
 * Henter kvitteringer fra Gmail-etiketten "Kvitteringer" og fra Drive-mappen
 * "ENK/Innboks", leser tekst (også bilder/skannede PDF-er via Drive-OCR),
 * arkiverer bilaget i "ENK/Bilag/ÅÅÅÅ" og fører en rad i fanen Utgifter.
 * Alle rader merkes "AUTO – kontroller" – du godkjenner dem selv.
 */

const OPPSETT = {
  gmailEtikett: 'Kvitteringer',
  gmailFerdig: 'Kvitteringer/Ført',
  // Mappene ligger i samme Drive-mappe som regnearket (ENK/).
  innboksMappe: 'Innboks',
  bilagMappe: 'Bilag',
  forsteRad: 2,
  sisteRad: 401,
};

const STANDARDREGLER = [
  ['openart, higgsfield, adobe, anthropic, claude, openai, github, fiken, conta, domeneshop, one.com', 'Programvare og abonnementer', ''],
  ['telenor, telia, ice, talkmore, altibox', 'Telefon og internett', 0.5],
  ['elkjøp, elkjop, komplett, power, proshop, kjell', 'Utstyr under 30 000 kr', ''],
  ['vy, flytoget, norwegian, sas, widerøe, ruter, hotel', 'Reise (tog, fly, hotell)', ''],
  ['facebook ads, google ads, tiktok ads, meta platforms', 'Reklame og markedsføring', ''],
  ['stripe, vipps, paypal, sumup', 'Bank- og betalingsgebyr', ''],
  ['posten, bring, postnord', 'Porto og frakt', ''],
  ['udemy, coursera, skillshare, adlibris', 'Kurs og faglitteratur', ''],
];

// ---------- Meny og tidsstyring ----------

function onOpen() {
  SpreadsheetApp.getUi().createMenu('ENK-robot')
    .addItem('Hent kvitteringer nå', 'kjorRobot')
    .addItem('Slå på automatisk kjøring (hver time)', 'installerTidsstyring')
    .addItem('Slå av automatisk kjøring', 'fjernTidsstyring')
    .addToUi();
}

function installerTidsstyring() {
  fjernTidsstyring();
  ScriptApp.newTrigger('kjorRobot').timeBased().everyHours(1).create();
  SpreadsheetApp.getActive().toast('Roboten kjører nå hver time.');
}

function fjernTidsstyring() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'kjorRobot')
    .forEach(t => ScriptApp.deleteTrigger(t));
}

// ---------- Hovedløp ----------

function kjorRobot() {
  const lås = LockService.getScriptLock();
  if (!lås.tryLock(30000)) return;
  try {
    const regler = hentRegler();
    const kvitteringer = [...fraGmail(), ...fraInnboks()];
    const rader = kvitteringer.map(k => lagRad(k, regler));
    if (rader.length) skrivRader(rader);
    logg(`Ferdig: ${rader.length} kvittering(er) ført.`);
    if (rader.length) SpreadsheetApp.getActive().toast(`${rader.length} kvittering(er) ført i Utgifter.`);
  } catch (e) {
    logg('FEIL: ' + e.message);
    throw e;
  } finally {
    lås.releaseLock();
  }
}

/** Returnerer [{dato, leverandor, blob, tekst}] og flytter e-posten til "Ført". */
function fraGmail() {
  const etikett = GmailApp.getUserLabelByName(OPPSETT.gmailEtikett);
  if (!etikett) return [];
  const ferdig = GmailApp.getUserLabelByName(OPPSETT.gmailFerdig) || GmailApp.createLabel(OPPSETT.gmailFerdig);
  const ut = [];
  etikett.getThreads(0, 50).forEach(tråd => {
    tråd.getMessages().forEach(m => {
      const leverandor = leverandorFraAvsender(m.getFrom());
      const vedlegg = m.getAttachments().filter(a => /pdf|image\//i.test(a.getContentType()));
      if (vedlegg.length) {
        vedlegg.forEach(a => ut.push({ dato: m.getDate(), leverandor, blob: a.copyBlob(), tekst: '' }));
      } else {
        // Mange abonnementer sender kvitteringen bare i e-postteksten: lagres som PDF.
        const html = `<h3>${m.getSubject()}</h3><p>Fra: ${m.getFrom()}<br>Dato: ${m.getDate()}</p>${m.getBody()}`;
        const pdf = Utilities.newBlob(html, 'text/html', 'kvittering.html').getAs('application/pdf');
        ut.push({ dato: m.getDate(), leverandor, blob: pdf, tekst: m.getPlainBody() });
      }
    });
    tråd.removeLabel(etikett).addLabel(ferdig);
  });
  return ut;
}

function fraInnboks() {
  const mappe = finnEllerLagMappe(enkMappe(), OPPSETT.innboksMappe);
  const ut = [];
  const filer = mappe.getFiles();
  while (filer.hasNext()) {
    const f = filer.next();
    const navn = f.getName().replace(/\.[^.]+$/, '');
    const m = navn.match(/^(20\d{2}-\d{2}-\d{2})_(.+)$/);
    ut.push({
      dato: m ? new Date(m[1] + 'T12:00:00') : null,
      leverandor: m ? m[2] : '',
      blob: f.getBlob(),
      tekst: '',
      kilde: f,
    });
  }
  return ut;
}

function lagRad(k, regler) {
  const tekst = k.tekst || lesTekst(k.blob);
  const dato = k.dato || finnDato(tekst) || new Date();
  const leverandor = trygtNavn(k.leverandor || gjettLeverandor(tekst));
  let { belop, valuta } = finnBelop(tekst);
  const regel = gjettKategori(regler, leverandor, tekst);
  const merknad = ['AUTO – kontroller'];
  if (belop === null) merknad.push('fant ikke beløp');
  if (valuta && valuta !== 'NOK') {
    merknad.push(`${valuta} ${belop.toFixed(2)} – før NOK-beløpet fra bankutskriften`);
    belop = null;
  }
  if (!regel.kategori) merknad.push('velg kategori');

  const fil = arkiver(k.blob, dato, leverandor);
  if (k.kilde) k.kilde.setTrashed(true);
  return [dato, `Kvittering ${leverandor}`, leverandor, regel.kategori, belop, regel.andel,
          `=HYPERLINK("${fil.getUrl()}","${fil.getName()}")`, 'Firmakonto', merknad.join('; ')];
}

function skrivRader(rader) {
  const ark = SpreadsheetApp.getActive().getSheetByName('Utgifter');
  const n = OPPSETT.sisteRad - OPPSETT.forsteRad + 1;
  const ab = ark.getRange(OPPSETT.forsteRad, 1, n, 2).getValues();
  const ledige = [];
  ab.forEach((r, i) => { if (r[0] === '' && r[1] === '') ledige.push(OPPSETT.forsteRad + i); });
  if (ledige.length < rader.length) throw new Error('Fanen Utgifter er full – utvid arket.');
  rader.forEach((r, i) => {
    const rad = ledige[i];
    ark.getRange(rad, 1, 1, 6).setValues([r.slice(0, 6)]);      // A–F
    ark.getRange(rad, 10).setFormula(r[6]);   // J bilag-lenke
    ark.getRange(rad, 11, 1, 2).setValues([[r[7], r[8]]]);       // K–L
  });
}

// ---------- Drive ----------

function arkiver(blob, dato, leverandor) {
  const år = String(dato.getFullYear());
  const rot = finnEllerLagMappe(enkMappe(), OPPSETT.bilagMappe);
  const mappe = finnEllerLagMappe(rot, år);
  const ext = (blob.getContentType() || '').split('/')[1] || 'pdf';
  const base = `${Utilities.formatDate(dato, Session.getScriptTimeZone(), 'yyyy-MM-dd')}_${leverandor}`;
  let navn = `${base}.${ext.replace('jpeg', 'jpg')}`;
  for (let i = 2; mappe.getFilesByName(navn).hasNext(); i++) navn = `${base}__${i}.${ext}`;
  return mappe.createFile(blob.setName(navn));
}

function enkMappe() {
  const foreldre = DriveApp.getFileById(SpreadsheetApp.getActive().getId()).getParents();
  return foreldre.hasNext() ? foreldre.next() : DriveApp.getRootFolder();
}

function finnEllerLagMappe(forelder, navn) {
  const it = forelder.getFoldersByName(navn);
  return it.hasNext() ? it.next() : forelder.createFolder(navn);
}

/** OCR via Drive (krever tjenesten "Drive API" under Tjenester i Apps Script). */
function lesTekst(blob) {
  try {
    const doc = Drive.Files.create(
      { name: 'ocr-tmp', mimeType: 'application/vnd.google-apps.document' },
      blob.copyBlob(), { ocrLanguage: 'no' });
    const tekst = DocumentApp.openById(doc.id).getBody().getText();
    DriveApp.getFileById(doc.id).setTrashed(true);
    return tekst;
  } catch (e) {
    logg('OCR feilet: ' + e.message);
    return '';
  }
}

// ---------- Regler og logg i regnearket ----------

function hentRegler() {
  const ss = SpreadsheetApp.getActive();
  let ark = ss.getSheetByName('Robot-regler');
  if (!ark) {
    ark = ss.insertSheet('Robot-regler');
    ark.getRange(1, 1, 1, 3).setValues([['Søkeord (kommaseparert)', 'Kategori', 'Næringsandel']]).setFontWeight('bold');
    ark.getRange(2, 1, STANDARDREGLER.length, 3).setValues(STANDARDREGLER);
    ark.getRange('C2:C200').setNumberFormat('0%');
    ark.setColumnWidth(1, 420); ark.setColumnWidth(2, 240);
  }
  return ark.getDataRange().getValues().slice(1)
    .filter(r => r[0] && r[1])
    .map(r => ({ ord: String(r[0]).split(',').map(s => s.trim()).filter(Boolean), kategori: r[1], andel: r[2] }));
}

function logg(tekst) {
  const ss = SpreadsheetApp.getActive();
  const ark = ss.getSheetByName('Robot-logg') || ss.insertSheet('Robot-logg');
  ark.appendRow([new Date(), tekst]);
}

// ---------- Ren tekstlogikk (testbar uten Google) ----------

function trygtNavn(t) {
  return String(t || '').toLowerCase().normalize('NFC')
    .replace(/[^\p{L}\p{N}-]+/gu, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'ukjent';
}

function leverandorFraAvsender(fra) {
  const m = String(fra).match(/^\s*"?([^"<]*?)"?\s*<([^>]+)>/);
  if (m && m[1]) return m[1];
  const adr = m ? m[2] : String(fra);
  return (adr.split('@')[1] || adr).split('.')[0];
}

function gjettLeverandor(tekst) {
  const linje = String(tekst).split('\n').map(s => s.trim()).find(s => /\p{L}{3,}/u.test(s));
  return linje ? linje.split(/\s+/)[0] : 'ukjent';
}

function gjettKategori(regler, leverandor, tekst) {
  const hay = `${leverandor} ${String(tekst).slice(0, 2000)}`.toLowerCase();
  for (const r of regler) {
    const treff = r.ord.some(o => new RegExp(`(^|[^\\p{L}\\p{N}])${o.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}($|[^\\p{L}\\p{N}])`, 'u').test(hay));
    if (treff) return { kategori: r.kategori, andel: r.andel === '' ? null : r.andel };
  }
  return { kategori: '', andel: null };
}

function tilTall(s) {
  s = s.replace(/[  ]/g, '');
  if (s.includes(',') && s.includes('.')) {
    s = s.lastIndexOf(',') > s.lastIndexOf('.') ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
  } else if (s.includes(',')) {
    s = s.replace(',', '.');
  } else if (/^\d{1,3}(\.\d{3})+$/.test(s)) {
    s = s.replace(/\./g, '');
  }
  return parseFloat(s);
}

function finnBelop(tekst) {
  const re = /(?:totalt|total|sum|å betale|a betale|beløp|amount paid|amount due|grand total)[^\d\n]{0,25}?(NOK|kr|USD|\$|EUR|€)?\s*(\d{1,3}(?:[ . ]\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)\s*(NOK|kr|USD|EUR|€)?/gi;
  let best = null;
  for (const m of String(tekst).matchAll(re)) {
    const v = tilTall(m[2]);
    if (isNaN(v)) continue;
    let val = (m[1] || m[3] || 'NOK').toUpperCase();
    val = { KR: 'NOK', $: 'USD', '€': 'EUR' }[val] || val;
    if (!best || v > best.belop) best = { belop: v, valuta: val };
  }
  return best || { belop: null, valuta: null };
}

function finnDato(tekst) {
  const m = String(tekst).match(/\b(\d{1,2})[./](\d{1,2})[./](20\d{2})\b|\b(20\d{2})-(\d{2})-(\d{2})\b/);
  if (!m) return null;
  const d = m[1] ? new Date(+m[3], +m[2] - 1, +m[1], 12) : new Date(+m[4], +m[5] - 1, +m[6], 12);
  return isNaN(d) ? null : d;
}

if (typeof module !== 'undefined') {
  module.exports = { trygtNavn, leverandorFraAvsender, gjettKategori, finnBelop, finnDato, tilTall };
}
