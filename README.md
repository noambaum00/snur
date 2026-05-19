# snur

פרויקט Raspberry Pi ללוקליזציית קול עם 4 מיקרופונים (דרך MCP3008), חישוב מיקום 2D בזמן אמת, והצגה בדף אינטרנט.

## מה כלול

- איסוף נתונים מ־MCP3008 ל־4 ערוצים (או סימולציה לפיתוח ללא חומרה).
- חישוב הפרשי זמן הגעה (TDOA) בין מיקרופונים.
- הערכת מיקום מקור הקול ב־2D בעזרת Grid Search.
- API ודף אינטרנט להצגה בזמן אמת.
- לוגים ודיאגנוסטיקה: עוצמות ערוצים והשהיות מחושבות.

## מבנה

- `/snur/config.py` – קונפיגורציה וטעינה מקובץ JSON.
- `/snur/audio.py` – קריאת MCP3008 / סימולציה.
- `/snur/localization.py` – עיבוד אות וחישובי מיקום.
- `/snur/service.py` – לולאת עיבוד רציפה ושמירת snapshot.
- `/snur/web.py` – שרת HTTP + UI.
- `/snur/__main__.py` – נקודת הרצה.
- `/tests/test_localization.py` – בדיקות בסיסיות.

## הרצה מהירה

```bash
cd /home/runner/work/snur/snur
python -m snur
```

ברירת המחדל רצה במצב סימולציה (`simulate=true`) על פורט `8080`.

פתח בדפדפן:

`http://<raspberry-pi-ip>:8080`

## קובץ קונפיגורציה (אופציונלי)

אפשר להעביר קובץ JSON:

```bash
python -m snur --config /path/to/config.json
```

דוגמה:

```json
{
  "simulate": false,
  "sample_rate_hz": 8000,
  "frame_size": 256,
  "speed_of_sound_mps": 343.0,
  "mic_positions": [[0.0, 0.0], [0.2, 0.0], [0.2, 0.2], [0.0, 0.2]],
  "search_bounds": [-1.5, 1.5, -1.5, 1.5],
  "search_step_m": 0.05,
  "channels": [0, 1, 2, 3],
  "spi_bus": 0,
  "spi_device": 0,
  "ui_bind_host": "0.0.0.0",
  "ui_bind_port": 8080,
  "calibration_offsets_s": [0.0, 0.0, 0.0, 0.0]
}
```

## הערות חומרה

- עבור מצב חומרה אמיתי, נדרש SPI פעיל ב־Raspberry Pi.
- המודול משתמש ב־`spidev` בזמן ריצה כאשר `simulate=false`.
- AGC במיקרופונים עלול להשפיע על דיוק TDOA; מומלץ כיול בשטח.

## בדיקות

```bash
cd /home/runner/work/snur/snur
python -m unittest discover -v
```
