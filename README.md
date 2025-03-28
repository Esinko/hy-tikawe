# Code Golf Club - HY tikawe project
> This repository contains University of Helsinki CS course work. Contents in Finnish.

**Nykytilanne**
Käyttäjä voi luoda tilin, kirjautua, luoda haasteita, muokata haasteita, poistaa haasteita ja äänestää haasteita.
Lisäksi käyttäjä voi katsella toisten profiileja ja katsella sekä muokata omaa profiiliaa.
Käyttäjä voi selata haasteita jostain tietystä tai kaikista kategoiroista ja etsiä haasteita hakusanalla.

### Sovelluksen toiminnot
- [X] Käyttäjä pystyy luomaan tunnukksen ja kirjautumaan sisään sovellukseen.
- [X] Käyttäjä voi luoda ja muokata omaa profiiliaan (kuvaus, profiilikuva ja taustakuva)
- Käyttäjä näkee äänestystilastoja profiilistaan
- [X] Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan haasteita.
- Käyttäjä pystyy lisäämään liitteitä haasteisiin
- [X] Käyttäjä näkee sovellukseen itse ja toisten käyttäjien toimesta julkaistut haasteet
- Käyttäjä pystyy etsimään haasteita hakusanalla
- Käyttäjä pystyy etsimään profiileja hakusanalla
- [X] Käyttäjä voi äänestää haasteita
- Käyttäjä voi luoda, muokata ja poistaa ratkaisuja
- Käyttäjä voi luoda, muokata ja poistaa kommentteja
- Käyttäjä voi äänestää ratkaisuja ja kommentteja

### Sovelluksen käyttö
Suorita sovellus:
```bash
$ python3 -m venv venv
$ source venv/bin/activate
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