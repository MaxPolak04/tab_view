# TabView

How to init migration:
flask db init
flask db migrate
flask db upgrade

zrobić freeze zainstalowanych paczek

## TODO:
- dokończyć testy
- upiększyć (pozmieniać kolory na te od eNki, większe teksty w inputach)
- środowisko wirtualne uv (?)


## Funkcje:
- CRUD użytkowników, mediów, urządzeń, eventów
- kalendarz pod urządzeniem
- kolejki zdjęć i filmów
- usuwanie starych eventów automatycznie
- podział na role - admin może dodawać użytkowników


## Zabezpieczenia:
- szyfrowanie formularzy
- zabezpieczenie basy danych przed SQLinjection
- API - ograniczona liczba zapytań na minutę
- podział na role
- zabezpieczone widoki
- jak ma wyglądać synchronizacja z czasem na serwerze?