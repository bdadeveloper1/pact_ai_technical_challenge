"""
gRPC Server for EHR Document Processing Service
Handles document generation, processing, and retrieval using Faker data
"""

import grpc
from concurrent import futures
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Import generated gRPC classes (will be generated from proto)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'generated'))

try:
    import ehr_service_pb2
    import ehr_service_pb2_grpc
except ImportError:
    # Fallback for development - create stubs
    print("Warning: gRPC generated files not found. Run 'python -m grpc_tools.protoc' to generate them.")
    ehr_service_pb2 = None
    ehr_service_pb2_grpc = None

from .data_generator import EHRDataGenerator, ProcessingState, FHIRVersion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EHRServiceImpl:
    """Implementation of EHR Service gRPC interface"""
    
    def __init__(self):
        self.data_generator = EHRDataGenerator()
        self.storage = {
            "patients": [],
            "resources": [],
            "derived_facts": []
        }
        logger.info("EHR Service initialized")
    
    def GenerateEHRData(self, request, context):
        """Generate mock EHR data using Faker"""
        try:
            logger.info(f"Generating EHR data for {request.num_patients} patients")
            
            # Generate complete dataset
            dataset = self.data_generator.generate_complete_dataset(
                num_patients=request.num_patients,
                min_resources=request.min_resources_per_patient,
                max_resources=request.max_resources_per_patient
            )
            
            # Store in memory (in production, would store in database)
            self.storage.update(dataset)
            
            # Convert to gRPC response
            resources = []
            for resource_data in dataset["resources"]:
                resource = self._dict_to_ehr_resource(resource_data)
                resources.append(resource)
            
            response = ehr_service_pb2.GetResourcesResponse(
                resources=resources,
                total_count=len(resources),
                has_more=False
            )
            
            logger.info(f"Generated {len(resources)} resources for {request.num_patients} patients")
            return response
            
        except Exception as e:
            logger.error(f"Error generating EHR data: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to generate EHR data: {str(e)}")
            return ehr_service_pb2.GetResourcesResponse()
    
    def GetResources(self, request, context):
        """Get EHR resources with filtering"""
        try:
            resources = self.storage["resources"]
            
            # Apply filters
            if request.patient_id:
                resources = [r for r in resources if r["metadata"]["identifier"]["patient_id"] == request.patient_id]
            
            if request.state_filter and request.state_filter != 0:  # 0 is UNSPECIFIED
                resources = [r for r in resources if r["metadata"]["state"] == request.state_filter]
            
            if request.resource_type_filter:
                resources = [r for r in resources if r["metadata"]["resource_type"] == request.resource_type_filter]
            
            # Apply pagination
            total_count = len(resources)
            start_idx = request.offset
            end_idx = start_idx + request.limit if request.limit > 0 else len(resources)
            paginated_resources = resources[start_idx:end_idx]
            
            # Convert to gRPC format
            grpc_resources = []
            for resource_data in paginated_resources:
                resource = self._dict_to_ehr_resource(resource_data)
                grpc_resources.append(resource)
            
            response = ehr_service_pb2.GetResourcesResponse(
                resources=grpc_resources,
                total_count=total_count,
                has_more=end_idx < total_count
            )
            
            logger.info(f"Returned {len(grpc_resources)} resources (total: {total_count})")
            return response
            
        except Exception as e:
            logger.error(f"Error getting resources: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get resources: {str(e)}")
            return ehr_service_pb2.GetResourcesResponse()
    
    def GetPatient(self, request, context):
        """Get patient profile by ID"""
        try:
            patients = self.storage["patients"]
            patient_data = next((p for p in patients if p["id"] == request.patient_id), None)
            
            if not patient_data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Patient {request.patient_id} not found")
                return ehr_service_pb2.PatientProfile()
            
            # Convert to gRPC format
            preferences = None
            if patient_data.get("preferences"):
                prefs = patient_data["preferences"]
                preferences = ehr_service_pb2.MatchPreferences(
                    preferred_location=prefs.get("preferred_location"),
                    willing_to_travel=prefs.get("willing_to_travel"),
                    condition_focus=prefs.get("condition_focus", []),
                    trial_phase_preference=prefs.get("trial_phase_preference", []),
                    trial_type=prefs.get("trial_type", [])
                )
            
            patient = ehr_service_pb2.PatientProfile(
                id=patient_data["id"],
                name=patient_data.get("name"),
                email=patient_data.get("email"),
                consent_given=patient_data["consent_given"],
                preferences=preferences,
                created_at=patient_data["created_at"]
            )
            
            logger.info(f"Retrieved patient {request.patient_id}")
            return patient
            
        except Exception as e:
            logger.error(f"Error getting patient: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get patient: {str(e)}")
            return ehr_service_pb2.PatientProfile()
    
    def GetDerivedFacts(self, request, context):
        """Get derived clinical facts for patient"""
        try:
            facts = self.storage["derived_facts"]
            patient_facts = next((f for f in facts if f["patient_id"] == request.patient_id), None)
            
            if not patient_facts:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Derived facts for patient {request.patient_id} not found")
                return ehr_service_pb2.DerivedClinicalFacts()
            
            # Convert to gRPC format
            diagnoses = []
            for diag in patient_facts["diagnoses"]:
                diagnosis = ehr_service_pb2.Diagnosis(
                    code=diag["code"],
                    text=diag["text"],
                    since=diag.get("since")
                )
                diagnoses.append(diagnosis)
            
            key_labs = ehr_service_pb2.KeyLabs(
                a1c=patient_facts["key_labs"].get("a1c"),
                egfr=patient_facts["key_labs"].get("egfr"),
                ldl=patient_facts["key_labs"].get("ldl"),
                sbp=patient_facts["key_labs"].get("sbp"),
                dbp=patient_facts["key_labs"].get("dbp")
            )
            
            derived_facts = ehr_service_pb2.DerivedClinicalFacts(
                patient_id=patient_facts["patient_id"],
                age_years=patient_facts["age_years"],
                sex=patient_facts["sex"],
                diagnoses=diagnoses,
                medications=patient_facts["medications"],
                key_labs=key_labs,
                exclusions=patient_facts["exclusions"],
                location=patient_facts["location"],
                extracted_at=patient_facts["extracted_at"]
            )
            
            logger.info(f"Retrieved derived facts for patient {request.patient_id}")
            return derived_facts
            
        except Exception as e:
            logger.error(f"Error getting derived facts: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get derived facts: {str(e)}")
            return ehr_service_pb2.DerivedClinicalFacts()
    
    def ProcessDocument(self, request, context):
        """Process a new document (simulate document intelligence)"""
        try:
            # In a real implementation, this would:
            # 1. Extract structured data from unstructured content using NLP
            # 2. Generate metadata and summaries
            # 3. Update derived clinical facts
            
            # For this demo, we'll simulate processing
            logger.info(f"Processing document for patient {request.patient_id}")
            
            # Generate a new resource based on the input
            resource_id = len(self.storage["resources"]) + 1
            processed_time = datetime.now()
            
            # Simulate AI summary generation
            ai_summary = self._generate_mock_ai_summary(request.resource_type, request.document_content)
            
            resource_data = {
                "metadata": {
                    "state": ProcessingState.PROCESSING_STATE_COMPLETED.value,
                    "created_time": processed_time.isoformat(),
                    "fetch_time": processed_time.isoformat(),
                    "processed_time": processed_time.isoformat(),
                    "identifier": {
                        "key": f"res_{request.patient_id}_{resource_id:04d}",
                        "uid": f"{resource_id:04d}",
                        "patient_id": request.patient_id
                    },
                    "resource_type": request.resource_type,
                    "version": FHIRVersion.FHIR_VERSION_R4.value
                },
                "human_readable_str": request.document_content[:500],  # Truncate for demo
                "ai_summary": ai_summary
            }
            
            # Store the processed resource
            self.storage["resources"].append(resource_data)
            
            # Generate/update derived facts (simplified)
            derived_facts_data = self._extract_mock_facts(request.patient_id, request.document_content)
            
            # Convert to gRPC response
            processed_resource = self._dict_to_ehr_resource(resource_data)
            derived_facts = self._dict_to_derived_facts(derived_facts_data)
            
            response = ehr_service_pb2.ProcessDocumentResponse(
                processed_resource=processed_resource,
                derived_facts=derived_facts
            )
            
            logger.info(f"Successfully processed document for patient {request.patient_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to process document: {str(e)}")
            return ehr_service_pb2.ProcessDocumentResponse()
    
    def _dict_to_ehr_resource(self, resource_data: Dict[str, Any]):
        """Convert dictionary to gRPC EHRResourceJson"""
        metadata = resource_data["metadata"]
        identifier = metadata["identifier"]
        
        grpc_identifier = ehr_service_pb2.EHRResourceIdentifier(
            key=identifier["key"],
            uid=identifier["uid"],
            patient_id=identifier["patient_id"]
        )
        
        grpc_metadata = ehr_service_pb2.EHRResourceMetadata(
            state=metadata["state"],
            created_time=metadata["created_time"],
            fetch_time=metadata["fetch_time"],
            processed_time=metadata.get("processed_time"),
            identifier=grpc_identifier,
            resource_type=metadata["resource_type"],
            version=metadata["version"]
        )
        
        return ehr_service_pb2.EHRResourceJson(
            metadata=grpc_metadata,
            human_readable_str=resource_data["human_readable_str"],
            ai_summary=resource_data.get("ai_summary")
        )
    
    def _dict_to_derived_facts(self, facts_data: Dict[str, Any]):
        """Convert dictionary to gRPC DerivedClinicalFacts"""
        # Implementation would convert facts dictionary to gRPC message
        # This is a simplified version for the demo
        return ehr_service_pb2.DerivedClinicalFacts(
            patient_id=facts_data["patient_id"],
            age_years=facts_data.get("age_years", 0),
            sex=facts_data.get("sex", "unknown")
        )
    
    def _generate_mock_ai_summary(self, resource_type: str, content: str) -> str:
        """Generate mock AI summary based on content"""
        if "diabetes" in content.lower():
            return "Diabetes management notes reviewed; monitoring blood glucose levels."
        elif "hypertension" in content.lower():
            return "Hypertension monitoring; blood pressure management ongoing."
        elif "lab" in resource_type.lower():
            return "Laboratory results show values within expected ranges for chronic conditions."
        else:
            return "Clinical documentation reviewed and processed successfully."
    
    def _extract_mock_facts(self, patient_id: str, content: str) -> Dict[str, Any]:
        """Extract mock clinical facts from document content"""
        return {
            "patient_id": patient_id,
            "age_years": 55,  # Mock extraction
            "sex": "female",
            "extracted_at": datetime.now().isoformat()
        }

def serve():
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    if ehr_service_pb2_grpc:
        ehr_service_pb2_grpc.add_EHRServiceServicer_to_server(
            EHRServiceImpl(), server
        )
    
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.stop(0)

if __name__ == "__main__":
    serve()
