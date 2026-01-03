# Funcționalități Platformă HA Config Manager

Acest document detaliază capabilitățile și modulele disponibile în platforma de management pentru Home Assistant.

## 1. Management Server (Orchestrator)
Modulul central pentru gestionarea instanțelor Home Assistant.
- **Gestionare Servere:** Adăugare, editare, ștergere și listare servere HA.
- **Conectivitate:**
  - Suport SSH (cu chei PPK/OpenSSH și parole).
  - Verificare status conexiune (Ping, SSH Latency, API Latency).
  - **Terminal Web:** Acces direct la linia de comandă a serverului prin browser (WebSSH).
- **Sincronizare Configurație:**
  - Descărcare automată a fișierelor de configurare (`.yaml`, `.json`, `.conf`) din server.
  - Stocare istoric versiuni configurație.

## 2. Backup & Restore
Sistem robust pentru protecția datelor.
- **Backup:**
  - Creare backup-uri manuale sau programate (Cron).
  - Suport pentru backup complet sau parțial.
  - Backup specific pentru configurațiile **NodeRED** și **Zigbee2MQTT**.
- **Restore:** Restaurare rapidă a backup-urilor anterioare.
- **Mentenanță:** Curățare automată a backup-urilor vechi (retenție configurabilă).

## 3. Deployment (Desfășurare)
Pipeline pentru aplicarea modificărilor de configurare.
- **Deploy:** Aplicarea controlată a modificărilor pe serverele de producție.
- **Validare:** Verificare configurație înainte de aplicare.
- **Rollback:** Revenire automată sau manuală la versiunea anterioară în caz de erori critice.
- **Istoric:** Jurnal complet al tuturor deploy-urilor efectuate.

## 4. Asistent AI (Deepseek Integration)
Asistent inteligent integrat pentru suport tehnic.
- **Chat:** Interfață de conversație pentru întrebări despre Home Assistant.
- **Troubleshooting:** Analiza automată a erorilor și sugestii de remediere.
- **Generare Cod:** Creare automată de scripturi, automatări și template-uri YAML.
- **Context:** AI-ul are acces la contextul configurației pentru răspunsuri personalizate.

## 5. Integrări Dispozitive Smart
Management centralizat pentru dispozitive DIY.

### ESPHome
- **Discovery:** Detectare automată a dispozitivelor ESPHome din rețea.
- **Update Firmware:** Actualizare OTA (Over-The-Air) pentru unul sau mai multe dispozitive simultan (Bulk Update).
- **Monitorizare:** Vizualizare status și log-uri dispozitive.

### WLED
- **Control:** Pornire/Oprire, schimbare culori și efecte.
- **Sincronizare:** Sincronizarea stării între mai multe controlere WLED.
- **Programare:** Orare (Schedules) pentru automatizarea luminilor.
- **Discovery:** Detectare automată în rețea.

## 6. Securitate & Rețea
- **Autentificare:** Sistem bazat pe utilizatori și roluri (JWT Tokens).
- **Criptare:** Datele sensibile (parole SSH, token-uri API, secrete) sunt stocate criptat în baza de date (Fernet encryption).
- **Tailscale:** Integrare pentru acces securizat de la distanță (VPN mesh).
- **Secrete:** Management centralizat al fișierului `secrets.yaml`.

## 7. Dashboard (Interfață Grafică)
- Interfață modernă (React/Next.js) pentru accesarea tuturor funcționalităților de mai sus.
- Statistici live despre starea serverelor și a serviciilor.
- Editor de cod/configurație integrat (pentru fișierele sincronizate).
