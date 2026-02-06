# TabView


## TODO:
- GitHub Actions i wdrożenie
- tagowanie media, filtry, tag pozostałe, nie da się dodać grafiki bez przypisania lub dodania tagu
- keep aspect ratio (nie może ucinać grafik)
- błędy nie będą trafiać do sysloga, tylko na stdin (tak mają kontenery)


## Funkcje:
- CRUD użytkowników, mediów, urządzeń, eventów
- harmonogramy
- kolejki zdjęć i filmów
- ręczne usuwanie starych eventów (by nie puchła baza danych)
- podział na role - admin może dodawać użytkowników
- możliwość przęłączania theme (light mode/dark mode)
- testy jednostkowe i integracyjne + mockowanie obiektów


## Zabezpieczenia:
- szyfrowanie formularzy
- zabezpieczenie basy danych przed SQLinjection
- API - ograniczona liczba zapytań na minutę
- podział użytkowników na role (admin/user)
- zabezpieczone widoki