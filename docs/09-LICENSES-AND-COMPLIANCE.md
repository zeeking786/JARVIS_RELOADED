# 9. Third-party licences and compliance

> This is a technical inventory, not legal advice. Have a lawyer review it before you sell. Check each licence and each service's terms again at the time of sale, because they change.

## Jarvis's own code

The Jarvis code in this folder has **no licence file yet**. Without one, nobody except the owner has any right to use it. Before you give a copy to a customer, decide the terms (for example a commercial end-user licence agreement) and add them as `LICENSE`. See the [selling checklist](11-SELLING-CHECKLIST.md).

## Software packages included or installed

All of these allow commercial use and redistribution under the conditions of their licence (mostly: keep the copyright notice and the licence text with the product). Versions are the ones the tests were run with.

### Backend (Python)

| Package | Version | Licence | Used for |
|---|---|---|---|
| FastAPI | 0.162.0 | MIT | The API |
| Starlette | 1.10.0 | BSD-3-Clause | Web layer under FastAPI |
| Pydantic | 2.14.2 | MIT | Request checking |
| Uvicorn | 0.54.0 | BSD-3-Clause | Web server |
| python-dotenv | 1.2.4 | BSD-3-Clause | Reads `.env` |
| python-multipart | 0.0.32 | Apache-2.0 | File uploads |
| Anthropic SDK | 2.3.0 | Apache-2.0 | Optional Claude calls |
| ChromaDB | 1.5.9 | Apache-2.0 | Document search database |
| ONNX Runtime | 1.31.1 | MIT | Runs the search model |
| python-docx | 1.2.0 | MIT | Word files |
| openpyxl | 3.1.5 | MIT | Excel files |
| python-pptx | 1.0.2 | MIT | PowerPoint files |
| pypdf | 6.21.4 | BSD-3-Clause | Reading PDFs |
| ReportLab | 5.1.0 | BSD | Making PDFs |
| Pillow | 13.0.0 | MIT-CMU (HPND) | Pictures |

Their own dependencies bring more packages. The full pinned list is `backend/requirements.lock.txt`. Before shipping, generate a full licence report (for example with `pip-licenses`) and include it.

### Front end (JavaScript)

| Package | Version | Licence |
|---|---|---|
| Next.js | 16.4.3 | MIT |
| React and React DOM | 19.3.1 | MIT |
| TypeScript (build only) | 7.0.2 | Apache-2.0 |

The Node packages that these install also carry licences (mostly MIT, ISC, BSD, Apache-2.0). Generate a report with `npx license-checker --summary` in `frontend` before shipping.

### Model and fonts

| Item | Licence or terms | Note |
|---|---|---|
| MiniLM sentence model (`all-MiniLM-L6-v2`, downloaded by ChromaDB on first use) | Apache-2.0 | About 80 MB, downloaded by the customer's computer, not shipped by you |
| Arial (Windows) | Microsoft font licence | Used when the studio makes a PDF. The font file is read from the customer's own Windows installation and is **not** redistributed with Jarvis |
| Calibri and other Word fonts | Microsoft | Only named in the Word file. The customer's Word supplies them |

## Outside services Jarvis contacts

These are used **without keys** because Jarvis is meant to cost nothing to run. Free access is a favour and not a contract, so each one needs a decision before you sell.

| Service | Used for | Terms to check | Risk for a paid product |
|---|---|---|---|
| **Open-Meteo** (`api.open-meteo.com`, `geocoding-api.open-meteo.com`) | Weather | Free use is offered for **non-commercial** use. Commercial use needs a paid plan and API key | **High.** Selling a product that calls the free endpoint is likely a breach. Buy a plan, let each customer enter their own key, or use another weather source |
| **Frankfurter** (`api.frankfurter.dev`) | Currency rates | Free, open-source service | Low. Check current terms; add a fallback because there is no guarantee of service |
| **Wikipedia** (`wikipedia.org`) | Answers to unknown questions | Text is licensed CC BY-SA 4.0 and the Wikimedia user-agent policy applies. Jarvis identifies itself as `JarvisAssistant/1.0` | Medium. Show attribution ("Source: Wikipedia") with answers, and keep the identifying user-agent. Add a contact address to it |
| **YouTube** (`youtube.com`) | Finding the first video for "play online ..." | YouTube's terms do not allow automated reading of its pages. The official way is the YouTube Data API with a key | **High.** The first-video lookup reads the search page. For a commercial release use the official API with the customer's key, or only open the search page, or remove the feature |
| **Google / Gmail** | Gmail draft link; SMTP sending | Using Gmail through a normal link, or SMTP with the customer's own account, is allowed | Low. Each customer uses their own account and app password |
| **Browser speech service** (Chrome: Google, Edge: Microsoft) | Voice recognition | A browser feature used by the page. The customer's browser vendor sets the terms | Medium. It sends audio to that vendor, so say so in your privacy notice. It is not available in every browser |
| **Anthropic (Claude)** | Optional written answers | Anthropic's commercial terms and usage policy apply to the key's owner | Low if each customer uses their own key. **Never ship your own key inside the product** |
| **Model download host** | MiniLM model, once | Terms of the host used by ChromaDB | Low. If your customers are offline, ship the model in the installer instead (Apache-2.0 allows it) |

## Name and branding

- **"Jarvis"** (and "J.A.R.V.I.S.", "Hey Jarvis") is the name of a fictional assistant owned by Marvel (Disney). Selling a product under that name, or using it in marketing, risks a trademark complaint. **Choose your own product name before selling.** The assistant's spoken name inside the program is changeable by the user, so you can keep "Jarvis" as an optional default only for private use.
- The word "Claude" and the Anthropic name belong to Anthropic. Mention them only to say the program can be connected to the service.
- The in-app icon and look are original to this project.

## Content you must not ship

Remove everything that is not the product and everything that contains secrets. Details in the [selling checklist](11-SELLING-CHECKLIST.md).

## Attributions to include with the product

Include (for example in a `NOTICE` file or an "About" page): the licences of the packages above, "Weather data by Open-Meteo.com" if you keep that service, "Contains text from Wikipedia, available under CC BY-SA 4.0" next to Wikipedia answers, and the Apache-2.0 notice for ChromaDB, the Anthropic SDK, python-multipart, TypeScript and the MiniLM model.

## Data protection

Jarvis keeps personal data (contacts, notes, documents) on the customer's own computer, and you (the seller) never receive it. That makes you a software supplier, not a processor of the customer's data, as long as you do not add features that send data to your own servers. If you add accounts, cloud sync, analytics or support uploads, privacy laws such as GDPR or India's DPDP Act will apply and you will need a privacy policy and consent screens.
