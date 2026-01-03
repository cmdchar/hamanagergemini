# Reguli de Proiect și Proceduri

Acest document definește standardele de lucru pentru proiectul HA Config Manager.

## 1. Documentație și Tracking
- **Verificare Pre-Execuție:** Înainte de a începe orice task sau comandă, verifică obligatoriu `progress.md`. Dacă funcționalitatea sau task-ul apare deja ca finalizat, informează utilizatorul despre acest lucru.
- **Actualizare Progres:** Orice modificare funcțională (cod, infrastructură, configurare) TREBUIE documentată imediat în fișierul `progress.md` din rădăcina proiectului.
- **Istoric:** `progress.md` servește ca sursă unică de adevăr pentru starea proiectului.
- **Documentare Completă (NOU):** Orice funcționalitate nouă sau modificare trebuie să fie documentată în trei locuri:
  1. **README.md**: Documentare tehnică și de ansamblu.
  2. **Interfață Utilizator (UI):** Adăugare info/help în pagina relevantă pentru ca utilizatorul să știe cum să folosească funcționalitatea.
  3. **Cunoștințe AI (System Prompt):** Asigură-te că AI-ul știe despre noua funcționalitate și poate răspunde la întrebări despre ea sau o poate executa.

## 2. Stil de Lucru (Bias for Action)
- **Proactivitate:** Nu aștepta confirmări pentru pași logici evidenți. Dacă o acțiune este necesară pentru a îndeplini obiectivul curent, execut-o.
- **Validare:** Testează întotdeauna modificările (unit tests sau scripturi de integrare) înainte de a considera task-ul complet.
- **Calitate peste Viteză:** Nu ne grăbim. Este mai bine să facem modificări corecte prima dată decât să reparăm 10 erori după.

## 3. Gestionarea Fișierelor
- **Fără fișiere inutile:** Nu crea fișiere `.md` (README, docs) decât la cerere explicită sau dacă sunt critice (ca acesta).
- **Editare vs Creare:** Preferă editarea fișierelor existente.

## 4. Consistență și Integritate Cod

### 4.1. Verificare End-to-End la Modificări
**OBLIGATORIU:** Când adaugi sau modifici cod, urmează acest checklist complet:

1. **Backend (Orchestrator):**
   - [ ] Model SQLAlchemy creat/modificat în `app/models/`
   - [ ] Model adăugat în `app/models/__init__.py` (export `__all__`)
   - [ ] Model importat în `app/db/session.py` → funcția `init_db()`
   - [ ] Schema Pydantic creată în `app/schemas/`
   - [ ] Endpoint API creat în `app/api/v1/`
   - [ ] Router inclus în `app/api/v1/__init__.py`
   - [ ] Toate import-urile necesare adăugate (typing: Dict, List, Optional, etc.)
   - [ ] Verificat că toate câmpurile schema corespund cu model
   - [ ] Test manual cu Postman/curl sau logs

2. **Frontend (Dashboard):**
   - [ ] Verificat endpoint-ul API folosit (prefix corect: `/servers/`, `/ha-config/`, `/ai/`)
   - [ ] Verificat parametrii query string (ex: `active_only`, `limit`, `skip`)
   - [ ] Type interfaces create/actualizate pentru response-uri
   - [ ] Query keys unice și consistente în React Query
   - [ ] Invalidate queries după mutații relevante
   - [ ] Error handling implementat (toast.error)
   - [ ] Loading states adăugate
   - [ ] UI components necesare importate
   - [ ] Test în browser (verificat Network tab, Console pentru erori)
   - [ ] **VERIFICARE UI VIZUALĂ**: Deschide pagina în browser și verifică că datele apar corect
   - [ ] **CONSOLE LOGS**: Adaugă console.log temporar pentru debugging (elimină înainte de commit)

3. **Integrări între Module:**
   - [ ] Dacă modifici un schema, verifică TOATE endpoint-urile care îl folosesc
   - [ ] Dacă adaugi câmp în model, actualizează toate schema-urile relevante
   - [ ] Dacă schimbi un endpoint path, caută în frontend TOATE utilizările (`grep -r`)
   - [ ] Verifică că formatul răspunsului backend se potrivește cu așteptările frontend

### 4.2. Principii de Consistență

**Schema Validation:**
- Orice modificare la un Pydantic schema TREBUIE să fie verificată în toate endpoint-urile care îl returnează
- Exemplu: `AIChatResponse` necesită `suggested_actions: List[AIAction]` → verifică că construiești obiectul corect

**Endpoint Paths:**
- Folosește prefix-ul corect: `/servers/`, `/ha-config/`, `/ai/`, `/ai/files/`
- Caută în frontend pentru ALL utilizările unui endpoint modificat
- Exemplu greșit: `/servers/{id}/configs` → Corect: `/ha-config/servers/{id}/configs`

**Import Dependencies:**
- ÎNTOTDEAUNA verifică că toate typing-urile sunt importate
- Exemplu: `List[Dict]` necesită `from typing import List, Dict`
- Nu presupune că sunt importate automat

**Database Models:**
- Orice model nou TREBUIE adăugat în 2 locuri:
  1. `app/models/__init__.py` - export în `__all__`
  2. `app/db/session.py` - import în `init_db()` pentru a crea tabelul

### 4.3. Procedură Anti-Erori

**Înainte de a considera task-ul complet:**
1. Restart ambele containere: `docker-compose restart orchestrator dashboard`
2. Verifică logs pentru erori: `docker logs ha-config-orchestrator -f`
3. Deschide browser → Console → verifică erori JavaScript
4. Deschide browser → Network tab → verifică 404/500 errors
5. Test funcționalitate completă (not just "code looks good")

**La întâlnirea unei erori:**
- Documentează cauza în acest fișier dacă este o greșeală tipică
- Adaugă check în checklist-ul de mai sus dacă este aplicabil

### 4.4. Exemple de Erori Întâlnite (Învățăminte)

**Eroare 1: Missing Type Import**
```python
# GREȘIT
def parse_file_modifications(ai_response: str) -> List[Dict]:
    # NameError: name 'Dict' is not defined

# CORECT
from typing import Dict, List
def parse_file_modifications(ai_response: str) -> List[Dict]:
```

**Eroare 2: Schema Mismatch**
```python
# GREȘIT - suggested_actions nu se potrivește cu AIAction schema
return AIChatResponse(
    suggested_actions=[{'id': '123', 'file_path': 'x.yaml'}]  # Lipsesc câmpuri obligatorii
)

# CORECT - toate câmpurile AIAction prezente
return AIChatResponse(
    suggested_actions=[{
        'action_type': 'file_modification',
        'action_params': {...},
        'description': '...',
        'requires_confirmation': True,
        'reversible': True,
    }]
)
```

**Eroare 3: Endpoint Path Inconsistență**
```typescript
// GREȘIT - prefix lipsește
const response = await apiClient.get(`/servers/${serverId}/configs`)

// CORECT - prefix complet
const response = await apiClient.get(`/ha-config/servers/${serverId}/configs`)
```

**Eroare 4: Model Nu se Creează în DB**
```python
# GREȘIT - model creat dar nu importat în init_db()
# Rezultat: tabelul nu se creează automat

# CORECT - model adăugat în app/db/session.py
from app.models import (
    ...,
    ai_file_modification,  # NOU
)
```

**Eroare 5: useEffect Dependencies Lipsă**
```typescript
// GREȘIT - useEffect fără dependency array sau cu dependencies incomplete
useEffect(() => {
  if (conversations && conversations.length > 0 && !conversationId) {
    setConversationId(conversations[0].id)
  }
}) // Lipsește dependency array - rulează la fiecare render!

// CORECT - dependency array complet
useEffect(() => {
  if (conversations && conversations.length > 0 && !conversationId) {
    setConversationId(conversations[0].id)
  }
}, [conversations, conversationId]) // Toate variabilele folosite
```

**Eroare 6: React Query Keys Inconsistente**
```typescript
// GREȘIT - query key nu se potrivește între queries
const { data } = useQuery({
  queryKey: ["messages", conversationId], // Key 1
  // ...
})
queryClient.invalidateQueries({ queryKey: ["ai-messages"] }) // Key diferit!

// CORECT - query keys consistente
const { data } = useQuery({
  queryKey: ["ai-messages", conversationId],
  // ...
})
queryClient.invalidateQueries({ queryKey: ["ai-messages", conversationId] })
```

**Eroare 7: Query Parameters Lipsă**
```typescript
// GREȘIT - backend filtrează cu active_only=true dar frontend nu specifică
const response = await apiClient.get("/ai/conversations")
// Rezultat: returnează doar conversații active, nu toate

// CORECT - specifică parametrii explicit
const response = await apiClient.get("/ai/conversations", {
  params: { active_only: false }
})
```

### 4.5. Reguli Suplimentare pentru Debugging

**Verificare Logs Înainte de Commit:**
```bash
# 1. Check orchestrator errors
docker logs ha-config-orchestrator 2>&1 | grep -i "error\|exception" | tail -20

# 2. Check dashboard build errors
docker logs ha-config-dashboard 2>&1 | grep -i "error\|failed" | tail -20

# 3. Restart și verificare clean startup
docker-compose restart orchestrator dashboard
docker logs ha-config-orchestrator 2>&1 | tail -10
docker logs ha-config-dashboard 2>&1 | tail -5
```

**Browser Console Must Be Clean:**
- Deschide DevTools → Console
- Refresh pagina
- NU trebuie să existe erori roșii (404, 500, JavaScript errors)
- Warnings (galbene) sunt acceptabile dar verifică relevanța

**Pydantic Validation Errors:**
- Când vezi "validation errors for [ModelName]", verifică IMEDIAT schema
- Compară câmpurile returnate cu cele definite în Pydantic model
- NU ignora "Field required" - înseamnă că lipsește câmp obligatoriu

**FastAPI Schema Debugging:**
- Verifică documentația auto-generată: `http://localhost:8081/api/docs`
- Testează endpoint-ul direct din Swagger UI
- Compară request/response body cu schema definită

## 5. Securitate
- **Chei și Secrete:** Nu comite niciodată chei reale în cod. Folosește variabile de mediu (`.env` sau `docker-compose.yml`).
- **Criptare:** Orice dată sensibilă (parole, token-uri) stocată în DB trebuie să fie criptată folosind `ENCRYPTION_KEY`.

## 6. Integrare AI Assistant
**OBLIGATORIU:** După orice modificare funcțională la platformă (nou endpoint, nouă funcționalitate, nou model de date):

1. **Actualizare Cunoștințe AI:**
   - Asigură-te că AI-ul are acces la funcționalitatea nouă prin endpoint-uri API
   - Verifică că AI poate citi, modifica sau folosi noua funcționalitate dacă este relevant
   - AI-ul trebuie să fie o enciclopedie completă a platformei - dacă există o funcționalitate, AI trebuie să știe despre ea

2. **Exemple de integrări necesare:**
   - Dacă adaugi un nou tip de entitate (ex: conversations, file modifications) → AI trebuie să poată lista, crea, modifica, șterge
   - Dacă adaugi un nou endpoint (ex: `/servers/{id}/logs`) → AI trebuie să știe să îl folosească pentru debugging
   - Dacă adaugi o nouă configurație (ex: WLED, FPP) → AI trebuie să poată ghida utilizatorul în configurarea acesteia

3. **Test AI Awareness:**
   - După implementare, testează prin AI Assistant dacă poate răspunde la întrebări despre noua funcționalitate
   - Exemplu: Dacă ai adăugat "pin conversation", întreabă AI-ul "Can I pin important conversations?" și verifică răspunsul

4. **Context Service:**
   - Dacă funcționalitatea nouă afectează contextul utilizatorului (ex: noi entități de monitorizat), actualizează `AIContextService`
   - Asigură-te că noile date apar în context când AI conversează cu utilizatorul

## 7. Documentație Funcționalități
**OBLIGATORIU:** Fiecare funcționalitate nouă trebuie documentată pentru utilizatori:

1. **UI Tooltips și Help Text:**
   - Butoane și acțiuni complexe trebuie să aibă tooltips explicative
   - Formulare trebuie să aibă placeholder text și descrieri clare
   - Mesaje de eroare trebuie să fie descriptive și să ghideze utilizatorul spre rezolvare

2. **In-App Documentation:**
   - Pentru funcționalități majore, adaugă secțiuni de "Help" sau "?" în UI
   - Exemplu: Un popover lângă "AI Modifications" care explică ce sunt și cum se folosesc

3. **README.md Updates:**
   - Actualizează README.md cu noile funcționalități adăugate
   - Include capturi de ecran sau GIF-uri unde este relevant
   - Documentează endpoint-urile API noi în secțiunea API

4. **Toast Messages:**
   - Folosește toast.success cu mesaje clare despre ce s-a întâmplat
   - Exemplu: "Conversation pinned successfully" nu doar "Success"
   - Pentru acțiuni cu consecințe, adaugă acțiuni în toast (ex: "Undo", "Review")

5. **Comentarii în Cod:**
   - Funcții complexe trebuie să aibă docstrings explicative
   - Logica business complicată trebuie comentată inline
   - Nu documenta cod evident (ex: "increment counter" pentru `count++`)

6. **Onboarding:**
   - Pentru utilizatori noi, consideră adăugarea de exemple sau "starter templates"
   - Empty states trebuie să ghideze utilizatorul ce să facă ("Click + to create first conversation")

**Principiu:** Un utilizator trebuie să poată folosi orice funcționalitate fără să consulte documentație externă sau cod sursă.
