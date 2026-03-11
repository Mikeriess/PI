# Arkitekturplan: Pi → TOASTER Split

## Protokol: MJPEG Relay (HTTP)

Pi streamer allerede MJPEG. TOASTER opretter **én** persisterende HTTP-forbindelse til Pi og videredistribuerer til N browserklienter. Pi ved aldrig, hvor mange der ser med.

```
[Webcam] → [Pi: port 8000] ──(1 stream)──→ [TOASTER: relay thread] → /video_feed
                                                                      → /video_feed
                                                                      → /video_feed (N klienter)
```

---

## Mappestruktur

```
/
├── pi/
│   ├── app.py             # Kun kamera + MJPEG, ingen viewer UI
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
└── toaster/
    ├── app.py             # Relay thread + Flask server
    ├── Dockerfile         # Ingen OpenCV/libgl1 nødvendig
    ├── docker-compose.yml
    ├── requirements.txt   # flask + requests (ingen opencv)
    └── templates/
        └── index.html     # Web UI
```

---

## Pi-komponent (minimale ændringer)

**Fjern fra nuværende `app.py`:**
- `/` route (inline HTML viewer) - Pi skal ikke serve UI
- `captured_images` periodik-gem logik - spild af disk-I/O

**Tilføj:**
- `/health` endpoint (returns `200 OK`) - TOASTER kan tjekke Pi er online

**`docker-compose.yml`:** Fjern `captured_images` volume mount. Ellers uændret.

---

## TOASTER-komponent (nyt)

**Relay-tråd** (`app.py`): En baggrundstråd der forbinder til Pi's `/video_feed`, parser MJPEG-frames via JPEG SOI/EOI markørerne (`\xff\xd8` / `\xff\xd9`), og gemmer seneste frame i `latest_frame`. Ved disconnect: automatisk reconnect efter 3 sekunder.

**Flask-server:** Genbruger Pi's `generate_frames`-mønster - serverer `latest_frame` til alle klienter.

**`requirements.txt`:** Kun `flask` + `requests` - ingen OpenCV. Langt mindre Docker image.

**`docker-compose.yml`:**
```yaml
environment:
  - PI_STREAM_URL=http://192.168.1.XX:8000/video_feed
```

---

## Service Discovery

**MVP:** Statisk IP via DHCP-reservation på routeren (tildel Pi en fast IP via MAC-adresse). TOASTER læser `PI_STREAM_URL` fra environment variabel / `.env` fil.

---

## Implementeringsrækkefølge

1. Opret `pi/` - test standalone (`/video_feed` virker i browser)
2. Opret `toaster/` - test relay mod Pi
3. Slet rod-niveau filer (`app.py`, `Dockerfile` osv.)
4. Commit begge komponenter

---

## Tekniske detaljer: Relay-logik

TOASTER's relay-tråd bruger JPEG SOI/EOI markørerne til frame-parsing:

- `\xff\xd8` = JPEG Start Of Image
- `\xff\xd9` = JPEG End Of Image

Denne metode er mere robust end multipart boundary-parsing og håndterer partielle chunk-reads korrekt. Buffer flushes ved 500KB for at forhindre memory-vækst ved korrupte frames.

Relay-tråden kører i en `while True` loop med `try/except` og 3 sekunders sleep ved fejl, så TOASTER automatisk genopretter forbindelsen hvis Pi genstarter.

---

## Fremtidige muligheder (ikke MVP)

- **Stream-indstillinger fra web UI:** TOASTER sender POST til Pi's `/settings` endpoint, som justerer OpenCV kameraparametre (opløsning, kvalitet, framerate)
- **Authentication:** HTTP Basic Auth decorator på TOASTER's Flask routes
- **Stats endpoint:** `/stats` returnerer JSON med klientantal, relay-status og frames/sek
- **mDNS discovery:** `avahi-daemon` på Pi-host giver `raspberrypi.local` hostname og fjerner kravet om statisk IP
