# Code Golf Club - HY tikawe project
> This repository contains University of Helsinki CS course work. Contents in Finnish.

### Sovelluksen toiminnot
- Käyttäjä pystyy luomaan tunnukksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä voi luoda ja muokata omaa profiiliaan (lempinimi, kuvaus, profiilikuva ja taustakuva)
- Käyttäjä näkee äänestystilastoja profiilistaan
- Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan haasteita.
- Käyttäjä pystyy lisäämään liitteitä haasteisiin
- Käyttäjä näkee sovellukseen itse ja toisten käyttäjien toimesta julkaistut haasteet, sekä niiden vastaukset, kommentit ja äänet.
- Käyttäjä pystyy etsimään haasteita hakusanalla
- Käyttäjä pystyy etsimään profiileja hakusanalla
- Käyttäjä voi luoda uuden haasteen, antaa sille nimen, kuvaukset, liitteet ja kategorian.
- Käyttäjä voi äänestää haasteita, niiden ratkaisuja ja kommentteja

### Sovelluksen käyttö
Suorita sovellus:
```bash
$ flask --app ./src/app.py run --debug
```

### Suunnitelma
Forum/kilpailu-sivusto, jossa käyttäjät voivat luoda ja osallistua code-golf haasteisiin.

Perinteisen code golfin sijaan sivulla on kategoriat:
- Least Lines of Javascript
- One Line of Javascript
- No Variable Declaration

- Etusivu
    - Haasteita ja vastauksia voi selata avoimesti, mutta oman ratkaisun lähetys vaatii rekisteröitymisen ja kirjautumisen.

- Haasteiden luonti
    - Vain kirjautuneet käyttäjät voivat luoda uusia haasteita.
    - Kirjautuneet käyttäjät voivat jättää haasteisiin myös kommentteja vastauksen sijaan
    - Kirjautuneet käyttäjät voivat poistaa/muokata vastauksia ja kommenttejaan

- Äänestäminen
    - Kirjautuneet käyttäjät voivat äänestää upvote/downvote metodilla ratkaisuja ja haasteita

- Profiilit
    - Rekisteröityessään käyttäjä luo itselleen profiilin
    - Kirjautunut käyttäjä voi muokata omaa profiiliaan
    - Rekisteröityessä valittu käyttäjänimi on muuttumaton ja uniikki
    - Muokattavia tietoja ovat lempinimi, kuvaus, profiilikuva ja profiilibanner
    - Profiilista näkyy kaikki käyttäjän haasteet, vastaukset ja kommentit
    - Profiilista näkyy käyttäjän saamien äänien summa