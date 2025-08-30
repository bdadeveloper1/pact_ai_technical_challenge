# EHR Document Extraction & Clinical Trial Matching MVP

A scalable document processing system for EHR data extraction and clinical trial matching, built with Python backend (FastAPI + gRPC) and Next.js frontend.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Next.js       │    │   Python Backend     │    │   Data Layer    │
│   Frontend      │◄──►│   FastAPI + gRPC     │◄──►│   Faker + Mock  │
│                 │    │                      │    │   Storage       │
│ • TanStack      │    │ • Document           │    │                 │
│   Table         │    │   Processing         │    │ • Patient       │
│ • Shadcn UI     │    │ • EHR Generation     │    │   Profiles      │
│ • React Query   │    │ • Clinical Facts     │    │ • EHR Resources │
│                 │    │   Extraction         │    │ • Derived Facts │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
```

## Project Structure

```
pact-ai_case_study/
├── backend/                 # Python backend services
│   ├── app/
│   │   ├── main.py         # FastAPI REST API
│   │   ├── grpc_server.py  # gRPC service implementation
│   │   └── data_generator.py # Faker-based EHR data generation
│   ├── protos/
│   │   └── ehr_service.proto # gRPC service definitions
│   ├── scripts/
│   │   ├── generate_grpc.py # Generate gRPC Python code
│   │   └── run_services.py  # Run both FastAPI and gRPC
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── types.ts    # TypeScript interfaces matching backend
│   │   │   └── api.ts      # API client for backend communication
│   │   └── components/     # React components (to be implemented)
│   └── package.json
└── README.md
```

## Key Features

### Backend (Python)

- **FastAPI REST API**: HTTP endpoints for frontend communication
- **gRPC Service**: High-performance internal service communication
- **Faker Data Generation**: Realistic EHR documents for diabetes/hypertension patients
- **Document Processing**: Simulated document intelligence with AI summaries
- **Clinical Facts Extraction**: Structured data extraction from unstructured documents

### Frontend (Next.js + TypeScript)

- **TanStack Table**: Performant data table with sorting, filtering, pagination
- **Shadcn UI**: Modern, accessible component library
- **React Query**: Optimized data fetching with caching and background updates
- **Expandable Rows**: Click to view detailed document content and AI summaries

## Data Model

### Core Types (matching PACT AI schema)

```typescript
interface EHRResourceJson {
  metadata: EHRResourceMetadata;
  humanReadableStr: string;
  aiSummary?: string;
}

interface EHRResourceMetadata {
  state: ProcessingState;
  createdTime: string;
  fetchTime: string;
  processedTime?: string;
  identifier: EHRResourceIdentifier;
  resourceType: string;
  version: FHIRVersion;
}
```

### Patient Archetypes

The system generates realistic patient data based on clinical archetypes:

1. **Type 2 Diabetes + Hypertension** (Female, 45-65)
   - Medications: Metformin, Lisinopril
   - A1C range: 7.8-9.2%

2. **Complex Diabetes + CVD** (Male, 50-70)
   - Medications: Metformin, Amlodipine, Atorvastatin
   - A1C range: 8.0-10.1%

3. **Early Diabetes** (Female, 40-60)
   - Medications: Metformin, Glipizide
   - A1C range: 7.2-8.5%

## Technical Decisions

### Why Python Backend + TypeScript Frontend?

- **Python**: Superior for ML/data processing, rich ecosystem for document intelligence
- **gRPC**: High-performance internal communication, type-safe contracts
- **FastAPI**: Fast development, automatic OpenAPI docs, excellent async support
- **TypeScript**: Type safety for complex data models, better developer experience

### Why This Architecture?

- **Separation of Concerns**: Clear boundaries between data processing and presentation
- **Scalability**: gRPC backend can scale independently, supports microservices
- **Type Safety**: Proto definitions ensure contract consistency between services
- **Real-world Ready**: Architecture supports future ML pipeline integration

## Setup & Development

### Quick Start (Recommended)

## ⚡ Quick Start (30 seconds)

### Prerequisites
- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend) - Install via [nvm](https://github.com/nvm-sh/nvm): `nvm install 18 && nvm use 18`

### One-Command Setup
```bash
./start-demo.sh
```

**This automatically starts both services and opens the app at http://localhost:3000**

---

## 🛠️ Manual Setup (If needed)

### Manual Setup

#### Terminal 1: Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Terminal 2: Frontend  
```bash
cd frontend
npm install
npm run dev
```

#### Access Points
- **🎨 Demo App**: http://localhost:3000
- **📊 API Docs**: http://localhost:8000/docs

## 🎯 Demo Flow (What You'll See)

1. **Home Page** → Auto-redirects to first patient
2. **Clinical Intelligence Dashboard**
   - Business metrics: Patient counts, trial eligibility, match scores
   - Clinical insights: Top conditions, trial readiness stats
3. **Patient Navigation** 
   - Click through 5 patient profiles from mid-tier US cities
   - Each patient has realistic preferences and medical conditions
4. **EHR Resources Table**
   - Interactive TanStack table with sorting, filtering, pagination
   - Click any row to expand and see:
     - Human-readable clinical content
     - AI-generated summaries  
     - Complete metadata panel
5. **Live Data Processing**
   - Medallion pipeline: Bronze → Silver → Gold data layers
   - Real-time statistics and quality metrics

---

## 🔧 Troubleshooting

### Common Issues

#### Node.js Version Error
```bash
# Error: "Node.js version >= v18.17.0 is required"
# Solution: Install Node.js 18+
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

#### Backend Won't Start
```bash
# Error: "ModuleNotFoundError" or "uvicorn not found"
# Solution: Install Python dependencies
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend Can't Connect
```bash
# Error: "Failed to fetch patients" or ECONNREFUSED
# Solution: Backend must be running first
curl http://localhost:8000/  # Should return JSON health check
```

#### "Site Can't Be Reached"
```bash
# Error: ERR_CONNECTION_REFUSED at localhost:3000
# Solution: Wait for frontend to fully start (can take 30-60 seconds)
# Look for: "Ready - started server on 0.0.0.0:3000"
```

---

## API Endpoints

### REST API (FastAPI)

**Core EHR Endpoints:**
- `GET /api/resources` - Get all EHR resources with filtering
- `GET /api/patients/{id}/resources` - Get patient-specific resources
- `GET /api/patients` - Get all patients
- `GET /api/patients/{id}/derived-facts` - Get clinical facts for trial matching
- `POST /api/generate-data` - Generate new mock data

**Medallion Architecture Endpoints:**
- `POST /api/process-document` - Process document through Bronze→Silver→Gold pipeline
- `GET /api/medallion/pipeline-stats` - Get transformation pipeline metrics
- `GET /api/medallion/gold-profiles` - Get business-ready patient profiles
- `GET /api/medallion/silver-entities` - Get extracted clinical entities

### gRPC Service

- `GenerateEHRData` - Generate mock EHR datasets
- `GetResources` - Query resources with filtering
- `ProcessDocument` - Document intelligence simulation
- `GetDerivedFacts` - Extract clinical trial matching facts

## Development Notes

### Time Investment
- **Estimated effort**: ~4 hours of focused development
- **Focus areas**: Clean architecture, realistic data generation, type safety

### Production Considerations

**Security & Compliance**:
- HIPAA compliance for PHI handling
- Authentication/authorization (OAuth2, RBAC)
- Audit logging for document access

**Scalability**:
- Firestore/PostgreSQL for persistent storage
- Redis for caching and session management
- Kubernetes deployment with horizontal scaling

**ML Integration**:
- Document OCR pipeline (PDF → text extraction)
- NLP models for clinical entity extraction
- Vector embeddings for semantic document search
- Clinical trial matching algorithms

**Data Pipeline**:
- ETL for real EHR integration (HL7 FHIR)
- Data validation and quality checks
- Batch processing for large document sets

## Next Steps

1. **Complete Frontend Implementation**:
   - TanStack Table with expandable rows
   - Filtering and search components
   - Document upload interface

2. **Enhanced Data Generation**:
   - More diverse patient conditions
   - Complex medication interactions
   - Realistic clinical trial criteria

3. **Document Intelligence**:
   - OCR integration for PDF processing
   - NLP models for entity extraction
   - Confidence scoring for AI summaries

4. **Clinical Trial Matching**:
   - Integration with ClinicalTrials.gov API
   - Matching algorithm implementation
   - Patient notification system

## Demo Scope

This implementation demonstrates:
- ✅ Scalable backend architecture with gRPC
- ✅ Realistic EHR data generation using Faker
- ✅ Type-safe API contracts between services
- ✅ Modern frontend development patterns
- ✅ Document processing simulation
- ✅ Clinical trial matching data model

**Not implemented** (production scope):
- Real document OCR/NLP processing
- Firestore integration
- Authentication/authorization
- Clinical trial matching algorithms
- Production deployment configuration

---

## 🎬 For PACT AI Team

###  Demo Video 
📹 **Loom Recording**:

**What you'll see:**
- Complete system demo with business intelligence dashboard
- Patient navigation and EHR resource exploration
- Technical architecture overview (Python backend, Medallion pipeline)
- UI/UX showcasing TanStack table, filtering, expandable rows

### Self-Setup Instructions
1. **Prerequisites Check**: `./verify-setup.sh` (optional but recommended)
2. **One-Command Start**: `./start-demo.sh` 
3. **Demo Navigation**: Follow the "Demo Flow" section above
4. **Troubleshooting**: Use troubleshooting guide if issues arise

### Key Technical Highlights
- **Scalable Architecture**: Python FastAPI + gRPC (ML/data engineering ready)
- **Medallion Pipeline**: Bronze→Silver→Gold for production data processing  
- **Business Intelligence**: Stakeholder metrics vs engineering metrics
- **Production Ready**: Docker/Railway/Render deployment configs included
- **Authentic Data**: Mid-tier US cities, realistic patient profiles

**⏱️ Time Investment**: ~4 hours (architecture depth over feature breadth)

---

*This project demonstrates technical architecture and data modeling capabilities for EHR document processing and clinical trial matching systems.*
