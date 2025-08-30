"""
FastAPI application that provides REST API endpoints
Connects to gRPC backend for EHR document processing
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import grpc
import asyncio
import logging
from datetime import datetime

# Import data generator for direct use (fallback when gRPC not available)
from .data_generator import EHRDataGenerator
from .medallion_pipeline import (
    MedallionTransformer, 
    BronzeDocument,
    create_medallion_pipeline,
    GoldPatientProfile
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EHR Document Processing API",
    description="REST API for EHR document extraction and clinical trial matching",
    version="1.0.0"
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
data_generator = EHRDataGenerator()
medallion_pipeline = create_medallion_pipeline()
mock_storage = {
    "patients": [],
    "resources": [],
    "derived_facts": [],
    "bronze_documents": [],
    "silver_entities": [],
    "gold_profiles": []
}

# Pydantic models matching TypeScript interfaces
class EHRResourceIdentifier(BaseModel):
    key: str
    uid: str
    patient_id: str = Field(alias="patientId")

class EHRResourceMetadata(BaseModel):
    state: int
    created_time: str = Field(alias="createdTime")
    fetch_time: str = Field(alias="fetchTime")
    processed_time: Optional[str] = Field(None, alias="processedTime")
    identifier: EHRResourceIdentifier
    resource_type: str = Field(alias="resourceType")
    version: int

class EHRResourceJson(BaseModel):
    metadata: EHRResourceMetadata
    human_readable_str: str = Field(alias="humanReadableStr")
    ai_summary: Optional[str] = Field(None, alias="aiSummary")

class MatchPreferences(BaseModel):
    preferred_location: Optional[str] = Field(None, alias="preferredLocation")
    willing_to_travel: Optional[bool] = Field(None, alias="willingToTravel")
    condition_focus: Optional[List[str]] = Field(None, alias="conditionFocus")
    trial_phase_preference: Optional[List[str]] = Field(None, alias="trialPhasePreference")
    trial_type: Optional[List[str]] = Field(None, alias="trialType")

class PatientProfile(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    consent_given: bool = Field(alias="consentGiven")
    preferences: Optional[MatchPreferences] = None
    created_at: str = Field(alias="createdAt")

class Diagnosis(BaseModel):
    code: str
    text: str
    since: Optional[str] = None

class KeyLabs(BaseModel):
    a1c: Optional[float] = None
    egfr: Optional[float] = Field(None, alias="eGFR")
    ldl: Optional[float] = None
    sbp: Optional[float] = None
    dbp: Optional[float] = None

class DerivedClinicalFacts(BaseModel):
    patient_id: str = Field(alias="patientId")
    age_years: int = Field(alias="ageYears")
    sex: str
    diagnoses: List[Diagnosis]
    medications: List[str]
    key_labs: KeyLabs = Field(alias="keyLabs")
    exclusions: List[str]
    location: str
    extracted_at: str = Field(alias="extractedAt")

class GenerateDataRequest(BaseModel):
    num_patients: int = Field(5, ge=1, le=10)
    min_resources_per_patient: int = Field(4, ge=1, le=10)
    max_resources_per_patient: int = Field(8, ge=1, le=15)
    condition_focus: List[str] = Field(["diabetes", "hypertension"])

class ProcessDocumentRequest(BaseModel):
    patient_id: str = Field(alias="patientId")
    resource_type: str = Field(alias="resourceType")
    document_content: str = Field(alias="documentContent")

# Utility function to connect to gRPC (optional)
async def get_grpc_client():
    """Get gRPC client connection (optional for demo)"""
    try:
        channel = grpc.aio.insecure_channel('localhost:50051')
        # Import generated stubs here when available
        return None  # Placeholder
    except Exception as e:
        logger.warning(f"gRPC connection failed: {e}. Using direct data generator.")
        return None

@app.on_event("startup")
async def startup_event():
    """Initialize mock data on startup"""
    logger.info("Initializing EHR API server...")
    
    # Generate initial mock data
    dataset = data_generator.generate_complete_dataset(
        num_patients=5,
        min_resources=4,
        max_resources=8
    )
    mock_storage.update(dataset)
    
    logger.info(f"Generated {len(mock_storage['patients'])} patients with {len(mock_storage['resources'])} resources")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "EHR Document Processing API",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_stats": {
            "patients": len(mock_storage["patients"]),
            "resources": len(mock_storage["resources"]),
            "derived_facts": len(mock_storage["derived_facts"])
        }
    }

@app.post("/api/generate-data")
async def generate_data(request: GenerateDataRequest, background_tasks: BackgroundTasks):
    """Generate new mock EHR data"""
    try:
        logger.info(f"Generating data for {request.num_patients} patients")
        
        # Generate data using Faker
        dataset = data_generator.generate_complete_dataset(
            num_patients=request.num_patients,
            min_resources=request.min_resources_per_patient,
            max_resources=request.max_resources_per_patient
        )
        
        # Update storage
        mock_storage.update(dataset)
        
        return {
            "success": True,
            "message": f"Generated {len(dataset['resources'])} resources for {request.num_patients} patients",
            "data": {
                "patients_count": len(dataset["patients"]),
                "resources_count": len(dataset["resources"]),
                "derived_facts_count": len(dataset["derived_facts"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate data: {str(e)}")

@app.get("/api/patients/{patient_id}/resources")
async def get_patient_resources(
    patient_id: str,
    state_filter: Optional[int] = Query(None, description="Filter by processing state"),
    resource_type_filter: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get EHR resources for a specific patient"""
    try:
        resources = mock_storage["resources"]
        
        # Filter by patient ID
        patient_resources = [r for r in resources if r["metadata"]["identifier"]["patient_id"] == patient_id]
        
        # Apply additional filters
        if state_filter is not None:
            patient_resources = [r for r in patient_resources if r["metadata"]["state"] == state_filter]
        
        if resource_type_filter:
            patient_resources = [r for r in patient_resources if r["metadata"]["resource_type"] == resource_type_filter]
        
        # Apply pagination
        total_count = len(patient_resources)
        paginated_resources = patient_resources[offset:offset + limit]
        
        # Convert to response format (match TypeScript schema)
        formatted_resources = []
        for resource in paginated_resources:
            formatted_resource = {
                "metadata": {
                    "state": resource["metadata"]["state"],
                    "createdTime": resource["metadata"]["created_time"],
                    "fetchTime": resource["metadata"]["fetch_time"],
                    "processedTime": resource["metadata"].get("processed_time"),
                    "identifier": {
                        "key": resource["metadata"]["identifier"]["key"],
                        "uid": resource["metadata"]["identifier"]["uid"],
                        "patientId": resource["metadata"]["identifier"]["patient_id"]
                    },
                    "resourceType": resource["metadata"]["resource_type"],
                    "version": resource["metadata"]["version"]
                },
                "humanReadableStr": resource["human_readable_str"],
                "aiSummary": resource.get("ai_summary")
            }
            formatted_resources.append(formatted_resource)
        
        return {
            "resources": formatted_resources,
            "totalCount": total_count,
            "hasMore": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting patient resources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get resources: {str(e)}")

@app.get("/api/resources")
async def get_all_resources(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    state_filter: Optional[int] = Query(None, description="Filter by processing state"),
    resource_type_filter: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all EHR resources with optional filtering"""
    try:
        resources = mock_storage["resources"]
        
        # Apply filters
        if patient_id:
            resources = [r for r in resources if r["metadata"]["identifier"]["patient_id"] == patient_id]
        
        if state_filter is not None:
            resources = [r for r in resources if r["metadata"]["state"] == state_filter]
        
        if resource_type_filter:
            resources = [r for r in resources if r["metadata"]["resource_type"] == resource_type_filter]
        
        # Apply pagination
        total_count = len(resources)
        paginated_resources = resources[offset:offset + limit]
        
        # Convert to response format
        formatted_resources = []
        for resource in paginated_resources:
            formatted_resource = {
                "metadata": {
                    "state": resource["metadata"]["state"],
                    "createdTime": resource["metadata"]["created_time"],
                    "fetchTime": resource["metadata"]["fetch_time"],
                    "processedTime": resource["metadata"].get("processed_time"),
                    "identifier": {
                        "key": resource["metadata"]["identifier"]["key"],
                        "uid": resource["metadata"]["identifier"]["uid"],
                        "patientId": resource["metadata"]["identifier"]["patient_id"]
                    },
                    "resourceType": resource["metadata"]["resource_type"],
                    "version": resource["metadata"]["version"]
                },
                "humanReadableStr": resource["human_readable_str"],
                "aiSummary": resource.get("ai_summary")
            }
            formatted_resources.append(formatted_resource)
        
        return {
            "resources": formatted_resources,
            "totalCount": total_count,
            "hasMore": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get resources: {str(e)}")

@app.get("/api/patients")
async def get_patients():
    """Get all patient profiles"""
    try:
        patients = mock_storage["patients"]
        
        # Convert to response format
        formatted_patients = []
        for patient in patients:
            formatted_patient = {
                "id": patient["id"],
                "name": patient.get("name"),
                "email": patient.get("email"),
                "consentGiven": patient["consent_given"],
                "preferences": patient.get("preferences"),
                "createdAt": patient["created_at"]
            }
            formatted_patients.append(formatted_patient)
        
        return {"patients": formatted_patients}
        
    except Exception as e:
        logger.error(f"Error getting patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get patients: {str(e)}")

@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get specific patient profile"""
    try:
        patients = mock_storage["patients"]
        patient = next((p for p in patients if p["id"] == patient_id), None)
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Convert to response format
        formatted_patient = {
            "id": patient["id"],
            "name": patient.get("name"),
            "email": patient.get("email"),
            "consentGiven": patient["consent_given"],
            "preferences": patient.get("preferences"),
            "createdAt": patient["created_at"]
        }
        
        return formatted_patient
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

@app.get("/api/patients/{patient_id}/derived-facts")
async def get_derived_facts(patient_id: str):
    """Get derived clinical facts for patient"""
    try:
        facts = mock_storage["derived_facts"]
        patient_facts = next((f for f in facts if f["patient_id"] == patient_id), None)
        
        if not patient_facts:
            raise HTTPException(status_code=404, detail=f"Derived facts for patient {patient_id} not found")
        
        # Convert to response format
        formatted_facts = {
            "patientId": patient_facts["patient_id"],
            "ageYears": patient_facts["age_years"],
            "sex": patient_facts["sex"],
            "diagnoses": patient_facts["diagnoses"],
            "medications": patient_facts["medications"],
            "keyLabs": patient_facts["key_labs"],
            "exclusions": patient_facts["exclusions"],
            "location": patient_facts["location"],
            "extractedAt": patient_facts["extracted_at"]
        }
        
        return formatted_facts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting derived facts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get derived facts: {str(e)}")

@app.post("/api/process-document")
async def process_document(request: ProcessDocumentRequest):
    """Process a new document using Medallion architecture"""
    try:
        logger.info(f"Processing document for patient {request.patient_id} using Medallion pipeline")
        
        # BRONZE LAYER: Create raw document
        doc_id = f"doc_{request.patient_id}_{len(mock_storage['bronze_documents']) + 1}"
        bronze_doc = BronzeDocument(
            document_id=doc_id,
            patient_id=request.patient_id,
            source_system="API_Upload",
            document_type=request.resource_type,
            raw_content=request.document_content
        )
        mock_storage["bronze_documents"].append(bronze_doc)
        
        # SILVER LAYER: Extract structured entities
        silver_entities = medallion_pipeline.bronze_to_silver_document(bronze_doc)
        mock_storage["silver_entities"].extend(silver_entities)
        
        # GOLD LAYER: Create business-ready profile (if patient exists)
        patients = mock_storage["patients"]
        patient = next((p for p in patients if p["id"] == request.patient_id), None)
        
        gold_profile = None
        if patient:
            demographics = {
                "age": 52,  # Would extract from patient record
                "sex": "female",
                "location": patient.get("preferences", {}).get("preferred_location", "unknown")
            }
            gold_profile = medallion_pipeline.silver_to_gold_patient(
                request.patient_id, silver_entities, demographics
            )
            
            # Update or add gold profile
            existing_gold = next((g for g in mock_storage["gold_profiles"] 
                                if hasattr(g, 'patient_id') and g.patient_id == request.patient_id), None)
            if existing_gold:
                mock_storage["gold_profiles"].remove(existing_gold)
            mock_storage["gold_profiles"].append(gold_profile)
        
        # Traditional resource creation for compatibility
        ai_summary = data_generator.generate_ai_summary(request.resource_type, request.document_content)
        resource_id = len(mock_storage["resources"]) + 1
        processed_time = datetime.now()
        
        resource_data = {
            "metadata": {
                "state": 3,  # PROCESSING_STATE_COMPLETED
                "created_time": processed_time.isoformat(),
                "fetch_time": processed_time.isoformat(),
                "processed_time": processed_time.isoformat(),
                "identifier": {
                    "key": f"res_{request.patient_id}_{resource_id:04d}",
                    "uid": f"{resource_id:04d}",
                    "patient_id": request.patient_id
                },
                "resource_type": request.resource_type,
                "version": 1
            },
            "human_readable_str": request.document_content[:500],
            "ai_summary": ai_summary
        }
        mock_storage["resources"].append(resource_data)
        
        # Response with medallion insights
        response = {
            "success": True,
            "message": f"Processed document through Medallion pipeline",
            "medallion_results": {
                "bronze_document_id": bronze_doc.document_id,
                "silver_entities_extracted": len(silver_entities),
                "gold_profile_updated": gold_profile is not None,
                "business_value": gold_profile._business_value if gold_profile else 0
            },
            "silver_entities": [
                {
                    "type": entity.entity_type,
                    "value": entity.entity_value,
                    "confidence": entity.confidence_score,
                    "code": entity.normalized_code
                } for entity in silver_entities
            ]
        }
        
        if gold_profile:
            response["gold_profile"] = {
                "patient_id": gold_profile.patient_id,
                "primary_conditions": gold_profile.primary_conditions,
                "medications": gold_profile.current_medications,
                "trial_eligibility": gold_profile.trial_eligibility_factors,
                "business_value": gold_profile._business_value
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/api/medallion/pipeline-stats")
async def get_pipeline_stats():
    """Get Medallion pipeline performance statistics"""
    try:
        stats = medallion_pipeline.get_pipeline_stats()
        storage_stats = {
            "bronze_documents": len(mock_storage["bronze_documents"]),
            "silver_entities": len(mock_storage["silver_entities"]),
            "gold_profiles": len(mock_storage["gold_profiles"])
        }
        
        return {
            "pipeline_stats": stats,
            "storage_stats": storage_stats,
            "data_quality": {
                "avg_entity_confidence": sum(e.confidence_score for e in mock_storage["silver_entities"]) / len(mock_storage["silver_entities"]) if mock_storage["silver_entities"] else 0,
                "avg_business_value": sum(g._business_value for g in mock_storage["gold_profiles"]) / len(mock_storage["gold_profiles"]) if mock_storage["gold_profiles"] else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting pipeline stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline stats: {str(e)}")

@app.get("/api/medallion/gold-profiles")
async def get_gold_profiles():
    """Get all Gold layer patient profiles"""
    try:
        profiles = []
        for profile in mock_storage["gold_profiles"]:
            profiles.append({
                "patient_id": profile.patient_id,
                "age_years": profile.age_years,
                "sex": profile.sex,
                "primary_conditions": profile.primary_conditions,
                "comorbidities": profile.comorbidities,
                "current_medications": profile.current_medications,
                "contraindications": profile.contraindications,
                "geographic_location": profile.geographic_location,
                "trial_eligibility_factors": profile.trial_eligibility_factors,
                "business_value": profile._business_value,
                "enriched_at": profile._enriched_at
            })
        
        return {"gold_profiles": profiles}
        
    except Exception as e:
        logger.error(f"Error getting gold profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get gold profiles: {str(e)}")

@app.get("/api/medallion/silver-entities")
async def get_silver_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID")
):
    """Get Silver layer extracted entities"""
    try:
        entities = mock_storage["silver_entities"]
        
        # Apply filters
        if entity_type:
            entities = [e for e in entities if e.entity_type == entity_type]
        
        # Note: Would need to track patient_id in entities for this filter
        # For now, this is a placeholder
        
        formatted_entities = []
        for entity in entities:
            formatted_entities.append({
                "entity_type": entity.entity_type,
                "entity_value": entity.entity_value,
                "confidence_score": entity.confidence_score,
                "extracted_from": entity.extracted_from,
                "normalized_code": entity.normalized_code,
                "quality_score": entity._quality_score,
                "processed_at": entity._processed_at
            })
        
        return {
            "silver_entities": formatted_entities,
            "total_count": len(formatted_entities)
        }
        
    except Exception as e:
        logger.error(f"Error getting silver entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get silver entities: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
