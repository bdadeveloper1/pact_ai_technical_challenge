"""
Medallion Architecture Implementation for EHR Document Processing
Bronze → Silver → Gold data transformation pipeline with dataclass decorators

This demonstrates production-ready data processing patterns for unstructured healthcare documents.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import re
import json
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ===== PIPELINE STAGE DECORATORS =====

def bronze_layer(cls):
    """
    Bronze Layer: Raw, unstructured data ingestion
    - Minimal validation
    - Preserve original format
    - Add ingestion metadata
    """
    @wraps(cls)
    def wrapper(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance._layer = "bronze"
        instance._ingested_at = datetime.now().isoformat()
        logger.debug(f"Bronze layer: Ingested {cls.__name__}")
        return instance
    
    # Add metadata to class
    wrapper._layer_type = "bronze"
    wrapper._description = "Raw data ingestion layer"
    return wrapper

def silver_layer(cls):
    """
    Silver Layer: Cleaned and validated data
    - Data quality checks
    - Standardized formats
    - Basic entity extraction
    """
    @wraps(cls)
    def wrapper(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance._layer = "silver"
        instance._processed_at = datetime.now().isoformat()
        instance._quality_score = instance._calculate_quality_score() if hasattr(instance, '_calculate_quality_score') else 1.0
        logger.debug(f"Silver layer: Processed {cls.__name__} (quality: {instance._quality_score})")
        return instance
    
    wrapper._layer_type = "silver"
    wrapper._description = "Cleaned and validated data layer"
    return wrapper

def gold_layer(cls):
    """
    Gold Layer: Business-ready, aggregated data
    - Clinical trial matching ready
    - Derived insights
    - Optimized for analytics
    """
    @wraps(cls)
    def wrapper(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance._layer = "gold"
        instance._enriched_at = datetime.now().isoformat()
        instance._business_value = instance._calculate_business_value() if hasattr(instance, '_calculate_business_value') else 1.0
        logger.debug(f"Gold layer: Enriched {cls.__name__} (business value: {instance._business_value})")
        return instance
    
    wrapper._layer_type = "gold"
    wrapper._description = "Business-ready analytics layer"
    return wrapper

# ===== BRONZE LAYER: RAW DATA STRUCTURES =====

@bronze_layer
@dataclass
class BronzeDocument:
    """Raw document as ingested from source systems"""
    document_id: str
    patient_id: str
    source_system: str
    document_type: str
    raw_content: str
    file_metadata: Dict[str, Any] = field(default_factory=dict)
    ingestion_timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.ingestion_timestamp:
            self.ingestion_timestamp = datetime.now().isoformat()

@bronze_layer
@dataclass
class BronzePatientRecord:
    """Raw patient data from EHR systems"""
    patient_id: str
    raw_demographics: Dict[str, Any]
    raw_clinical_data: List[Dict[str, Any]]
    source_ehr_system: str
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

# ===== SILVER LAYER: CLEANED DATA STRUCTURES =====

@silver_layer
@dataclass
class SilverClinicalEntity:
    """Extracted and validated clinical entities"""
    entity_type: str  # "medication", "diagnosis", "lab_value", etc.
    entity_value: str
    confidence_score: float
    extracted_from: str  # source text
    normalized_code: Optional[str] = None  # ICD-10, RxNorm, etc.
    temporal_info: Optional[Dict[str, Any]] = None
    
    def _calculate_quality_score(self) -> float:
        """Calculate data quality based on confidence and normalization"""
        base_score = self.confidence_score
        if self.normalized_code:
            base_score += 0.2
        if self.temporal_info:
            base_score += 0.1
        return min(base_score, 1.0)

@silver_layer
@dataclass
class SilverLabResult:
    """Structured lab result with validation"""
    test_name: str
    value: Union[float, str]
    unit: Optional[str]
    reference_range: Optional[str]
    test_date: str
    abnormal_flag: Optional[str] = None
    loinc_code: Optional[str] = None
    
    def _calculate_quality_score(self) -> float:
        """Assess lab result completeness and validity"""
        score = 0.6  # Base score
        if self.unit: score += 0.1
        if self.reference_range: score += 0.1
        if self.abnormal_flag: score += 0.1
        if self.loinc_code: score += 0.2
        return score

@silver_layer
@dataclass
class SilverMedication:
    """Structured medication with dosage information"""
    medication_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    route: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    rxnorm_code: Optional[str] = None
    
    def _calculate_quality_score(self) -> float:
        """Assess medication data completeness"""
        required_fields = [self.medication_name, self.dosage, self.frequency]
        present_required = sum(1 for field in required_fields if field)
        optional_score = sum(0.1 for field in [self.route, self.start_date, self.rxnorm_code] if field)
        return (present_required / len(required_fields)) * 0.7 + optional_score

@silver_layer
@dataclass
class SilverDiagnosis:
    """Structured diagnosis with coding"""
    diagnosis_text: str
    icd10_code: Optional[str]
    diagnosis_date: Optional[str]
    diagnosis_type: str = "primary"  # primary, secondary, comorbidity
    confidence_score: float = 1.0
    
    def _calculate_quality_score(self) -> float:
        """Assess diagnosis data quality"""
        score = self.confidence_score * 0.6
        if self.icd10_code: score += 0.3
        if self.diagnosis_date: score += 0.1
        return score

# ===== GOLD LAYER: BUSINESS-READY DATA =====

@gold_layer
@dataclass
class GoldPatientProfile:
    """Clinical trial matching ready patient profile"""
    patient_id: str
    age_years: int
    sex: str
    primary_conditions: List[str]
    comorbidities: List[str]
    current_medications: List[str]
    contraindications: List[str]
    geographic_location: str
    trial_eligibility_factors: Dict[str, Any] = field(default_factory=dict)
    
    def _calculate_business_value(self) -> float:
        """Calculate readiness for clinical trial matching"""
        completeness = sum([
            bool(self.primary_conditions),
            bool(self.current_medications),
            bool(self.geographic_location),
            bool(self.age_years),
            bool(self.sex)
        ]) / 5
        
        richness = min(len(self.primary_conditions) * 0.2 + 
                      len(self.comorbidities) * 0.1 + 
                      len(self.current_medications) * 0.1, 1.0)
        
        return (completeness * 0.7) + (richness * 0.3)

@gold_layer
@dataclass
class GoldClinicalSummary:
    """Aggregated clinical insights for decision support"""
    patient_id: str
    condition_severity: Dict[str, str]  # condition -> severity
    medication_adherence_signals: Dict[str, float]
    lab_trends: Dict[str, List[Dict[str, Any]]]
    risk_factors: List[str]
    trial_match_probability: float
    summary_generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def _calculate_business_value(self) -> float:
        """Calculate clinical decision support value"""
        completeness = sum([
            bool(self.condition_severity),
            bool(self.medication_adherence_signals),
            bool(self.lab_trends),
            bool(self.risk_factors)
        ]) / 4
        
        return completeness * 0.8 + min(self.trial_match_probability, 0.2)

# ===== TRANSFORMATION PIPELINE =====

class MedallionTransformer:
    """Orchestrates Bronze → Silver → Gold transformations"""
    
    def __init__(self):
        self.transformation_log = []
    
    def bronze_to_silver_document(self, bronze_doc: BronzeDocument) -> List[SilverClinicalEntity]:
        """Transform raw document content into structured clinical entities"""
        entities = []
        
        # Simulate NLP extraction (in production, use spaCy, transformers, etc.)
        entities.extend(self._extract_medications(bronze_doc.raw_content))
        entities.extend(self._extract_diagnoses(bronze_doc.raw_content))
        entities.extend(self._extract_lab_values(bronze_doc.raw_content))
        
        self._log_transformation("bronze_to_silver", bronze_doc.document_id, len(entities))
        return entities
    
    def silver_to_gold_patient(self, 
                              patient_id: str,
                              entities: List[SilverClinicalEntity],
                              demographics: Dict[str, Any]) -> GoldPatientProfile:
        """Aggregate silver entities into gold patient profile"""
        
        # Extract medications
        medications = [e.entity_value for e in entities if e.entity_type == "medication"]
        
        # Extract diagnoses
        diagnoses = [e.entity_value for e in entities if e.entity_type == "diagnosis"]
        primary_conditions = diagnoses[:3]  # Top 3 as primary
        comorbidities = diagnoses[3:]
        
        # Extract contraindications
        contraindications = [e.entity_value for e in entities if e.entity_type == "contraindication"]
        
        # Build trial eligibility factors
        eligibility_factors = {
            "diabetes_controlled": self._assess_diabetes_control(entities),
            "renal_function": self._assess_renal_function(entities),
            "cardiac_risk": self._assess_cardiac_risk(entities)
        }
        
        gold_profile = GoldPatientProfile(
            patient_id=patient_id,
            age_years=demographics.get("age", 0),
            sex=demographics.get("sex", "unknown"),
            primary_conditions=primary_conditions,
            comorbidities=comorbidities,
            current_medications=medications,
            contraindications=contraindications,
            geographic_location=demographics.get("location", "unknown"),
            trial_eligibility_factors=eligibility_factors
        )
        
        self._log_transformation("silver_to_gold", patient_id, gold_profile._business_value)
        return gold_profile
    
    # ===== EXTRACTION METHODS (Simulate NLP) =====
    
    def _extract_medications(self, text: str) -> List[SilverClinicalEntity]:
        """Extract medication entities from text"""
        # Simplified regex-based extraction (production would use NLP models)
        med_patterns = [
            r"(metformin)\s+(\d+\s*mg)?",
            r"(lisinopril)\s+(\d+\s*mg)?",
            r"(atorvastatin)\s+(\d+\s*mg)?",
            r"(amlodipine)\s+(\d+\s*mg)?",
            r"(glipizide)\s+(\d+\s*mg)?",
            r"(losartan)\s+(\d+\s*mg)?",
            r"(semaglutide)\s+(\d+\s*mg)?"
        ]
        
        medications = []
        for pattern in med_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                med_name = match.group(1)
                dosage = match.group(2) if len(match.groups()) > 1 else None
                
                entity = SilverClinicalEntity(
                    entity_type="medication",
                    entity_value=f"{med_name} {dosage}".strip() if dosage else med_name,
                    confidence_score=0.9,
                    extracted_from=match.group(0),
                    normalized_code=self._get_rxnorm_code(med_name)
                )
                medications.append(entity)
        
        return medications
    
    def _extract_diagnoses(self, text: str) -> List[SilverClinicalEntity]:
        """Extract diagnosis entities from text"""
        diagnosis_patterns = [
            (r"type\s+2\s+diabetes", "E11.9", "Type 2 Diabetes"),
            (r"hypertension", "I10", "Essential Hypertension"),
            (r"hyperlipidemia", "E78.5", "Hyperlipidemia"),
            (r"chronic\s+kidney\s+disease", "N18.3", "Chronic kidney disease"),
            (r"obesity", "E66.9", "Obesity")
        ]
        
        diagnoses = []
        for pattern, icd_code, standard_name in diagnosis_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                entity = SilverClinicalEntity(
                    entity_type="diagnosis",
                    entity_value=standard_name,
                    confidence_score=0.95,
                    extracted_from=match.group(0),
                    normalized_code=icd_code
                )
                diagnoses.append(entity)
        
        return diagnoses
    
    def _extract_lab_values(self, text: str) -> List[SilverClinicalEntity]:
        """Extract lab values from text"""
        lab_patterns = [
            (r"a1c:?\s*(\d+\.?\d*)\s*%", "hemoglobin_a1c"),
            (r"glucose:?\s*(\d+)\s*mg/dl", "glucose"),
            (r"creatinine:?\s*(\d+\.?\d*)\s*mg/dl", "creatinine"),
            (r"egfr:?\s*(\d+)", "egfr"),
            (r"ldl:?\s*(\d+)", "ldl_cholesterol"),
            (r"hdl:?\s*(\d+)", "hdl_cholesterol")
        ]
        
        lab_values = []
        for pattern, lab_name in lab_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                value = match.group(1)
                entity = SilverClinicalEntity(
                    entity_type="lab_value",
                    entity_value=f"{lab_name}: {value}",
                    confidence_score=0.85,
                    extracted_from=match.group(0),
                    normalized_code=self._get_loinc_code(lab_name)
                )
                lab_values.append(entity)
        
        return lab_values
    
    # ===== CLINICAL ASSESSMENT METHODS =====
    
    def _assess_diabetes_control(self, entities: List[SilverClinicalEntity]) -> str:
        """Assess diabetes control based on A1C values"""
        a1c_entities = [e for e in entities if "hemoglobin_a1c" in e.entity_value]
        if not a1c_entities:
            return "unknown"
        
        # Extract A1C value
        try:
            a1c_text = a1c_entities[0].entity_value
            a1c_value = float(re.search(r"(\d+\.?\d*)", a1c_text).group(1))
            
            if a1c_value < 7.0:
                return "well_controlled"
            elif a1c_value < 8.0:
                return "moderately_controlled"
            else:
                return "poorly_controlled"
        except:
            return "unknown"
    
    def _assess_renal_function(self, entities: List[SilverClinicalEntity]) -> str:
        """Assess kidney function based on eGFR"""
        egfr_entities = [e for e in entities if "egfr" in e.entity_value]
        if not egfr_entities:
            return "unknown"
        
        try:
            egfr_text = egfr_entities[0].entity_value
            egfr_value = float(re.search(r"(\d+)", egfr_text).group(1))
            
            if egfr_value >= 90:
                return "normal"
            elif egfr_value >= 60:
                return "mild_impairment"
            elif egfr_value >= 30:
                return "moderate_impairment"
            else:
                return "severe_impairment"
        except:
            return "unknown"
    
    def _assess_cardiac_risk(self, entities: List[SilverClinicalEntity]) -> str:
        """Assess cardiovascular risk factors"""
        risk_factors = []
        
        # Check for hypertension
        if any("hypertension" in e.entity_value.lower() for e in entities if e.entity_type == "diagnosis"):
            risk_factors.append("hypertension")
        
        # Check for hyperlipidemia
        if any("hyperlipidemia" in e.entity_value.lower() for e in entities if e.entity_type == "diagnosis"):
            risk_factors.append("hyperlipidemia")
        
        # Check for diabetes
        if any("diabetes" in e.entity_value.lower() for e in entities if e.entity_type == "diagnosis"):
            risk_factors.append("diabetes")
        
        if len(risk_factors) >= 3:
            return "high"
        elif len(risk_factors) >= 2:
            return "moderate"
        elif len(risk_factors) >= 1:
            return "low"
        else:
            return "minimal"
    
    # ===== UTILITY METHODS =====
    
    def _get_rxnorm_code(self, medication: str) -> Optional[str]:
        """Mock RxNorm code lookup"""
        rxnorm_codes = {
            "metformin": "6809",
            "lisinopril": "29046",
            "atorvastatin": "83367",
            "amlodipine": "17767"
        }
        return rxnorm_codes.get(medication.lower())
    
    def _get_loinc_code(self, lab_name: str) -> Optional[str]:
        """Mock LOINC code lookup"""
        loinc_codes = {
            "hemoglobin_a1c": "4548-4",
            "glucose": "2345-7",
            "creatinine": "2160-0",
            "egfr": "33914-3"
        }
        return loinc_codes.get(lab_name)
    
    def _log_transformation(self, stage: str, entity_id: str, metric: Any):
        """Log transformation for monitoring and debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "entity_id": entity_id,
            "metric": metric
        }
        self.transformation_log.append(log_entry)
        logger.info(f"Transformation: {stage} - {entity_id} - {metric}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics"""
        if not self.transformation_log:
            return {"total_transformations": 0}
        
        stages = {}
        for entry in self.transformation_log:
            stage = entry["stage"]
            if stage not in stages:
                stages[stage] = {"count": 0, "avg_metric": 0}
            stages[stage]["count"] += 1
            
        return {
            "total_transformations": len(self.transformation_log),
            "stages": stages,
            "last_transformation": self.transformation_log[-1]["timestamp"]
        }

# ===== PIPELINE FACTORY =====

def create_medallion_pipeline() -> MedallionTransformer:
    """Factory function to create configured pipeline"""
    return MedallionTransformer()

# ===== DEMO FUNCTION =====

def demo_medallion_pipeline():
    """Demonstrate the medallion architecture in action"""
    print("🏗️ Medallion Architecture Demo")
    print("=" * 50)
    
    # Create pipeline
    pipeline = create_medallion_pipeline()
    
    # Bronze layer: Raw document
    bronze_doc = BronzeDocument(
        document_id="doc_001",
        patient_id="P001",
        source_system="Epic_EHR",
        document_type="clinical_note",
        raw_content="""
        Patient: 52-year-old female with Type 2 Diabetes since 2017 and hypertension since 2019.
        Current medications: Metformin 1000 mg BID, Lisinopril 10 mg daily.
        Recent labs: A1C: 8.2%, Glucose: 162 mg/dL, Creatinine: 1.0 mg/dL, eGFR: 86.
        """
    )
    
    print(f"✅ Bronze: Ingested document {bronze_doc.document_id}")
    
    # Silver layer: Extract entities
    silver_entities = pipeline.bronze_to_silver_document(bronze_doc)
    print(f"✅ Silver: Extracted {len(silver_entities)} clinical entities")
    
    for entity in silver_entities:
        print(f"   - {entity.entity_type}: {entity.entity_value} (confidence: {entity.confidence_score})")
    
    # Gold layer: Create patient profile
    demographics = {"age": 52, "sex": "female", "location": "California"}
    gold_profile = pipeline.silver_to_gold_patient("P001", silver_entities, demographics)
    
    print(f"✅ Gold: Created patient profile (business value: {gold_profile._business_value:.2f})")
    print(f"   - Primary conditions: {gold_profile.primary_conditions}")
    print(f"   - Medications: {gold_profile.current_medications}")
    print(f"   - Trial eligibility: {gold_profile.trial_eligibility_factors}")
    
    # Pipeline stats
    stats = pipeline.get_pipeline_stats()
    print(f"\n📊 Pipeline Stats: {stats}")

if __name__ == "__main__":
    demo_medallion_pipeline()
