"""
EHR Data Generator using Faker library for realistic medical records.
Focuses on diabetes/hypertension use case for clinical trial matching.
"""

from faker import Faker
from faker.providers import BaseProvider
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from dataclasses import dataclass
from enum import Enum

fake = Faker()

class ProcessingState(Enum):
    PROCESSING_STATE_UNSPECIFIED = 0
    PROCESSING_STATE_NOT_STARTED = 1
    PROCESSING_STATE_PROCESSING = 2
    PROCESSING_STATE_COMPLETED = 3
    PROCESSING_STATE_FAILED = 4

class FHIRVersion(Enum):
    FHIR_VERSION_UNSPECIFIED = 0
    FHIR_VERSION_R4 = 1
    FHIR_VERSION_R4B = 2

@dataclass
class PatientArchetype:
    age_range: tuple[int, int]
    sex: str
    diagnoses: List[Dict[str, str]]
    medications: List[str]
    a1c_range: tuple[float, float]
    condition_focus: List[str]

# Patient archetypes for diabetes/hypertension
PATIENT_ARCHETYPES = [
    PatientArchetype(
        age_range=(45, 65),
        sex="female",
        diagnoses=[
            {"code": "E11.9", "text": "Type 2 Diabetes without complications", "since": "2017"},
            {"code": "I10", "text": "Essential Hypertension", "since": "2019"}
        ],
        medications=["metformin", "lisinopril"],
        a1c_range=(7.8, 9.2),
        condition_focus=["type 2 diabetes", "hypertension"]
    ),
    PatientArchetype(
        age_range=(50, 70),
        sex="male",
        diagnoses=[
            {"code": "E11.9", "text": "Type 2 Diabetes without complications", "since": "2015"},
            {"code": "I10", "text": "Essential Hypertension", "since": "2018"},
            {"code": "E78.5", "text": "Hyperlipidemia", "since": "2020"}
        ],
        medications=["metformin", "amlodipine", "atorvastatin"],
        a1c_range=(8.0, 10.1),
        condition_focus=["type 2 diabetes", "cardiovascular disease"]
    ),
    PatientArchetype(
        age_range=(40, 60),
        sex="female",
        diagnoses=[
            {"code": "E11.9", "text": "Type 2 Diabetes without complications", "since": "2020"}
        ],
        medications=["metformin", "glipizide"],
        a1c_range=(7.2, 8.5),
        condition_focus=["type 2 diabetes"]
    ),
    PatientArchetype(
        age_range=(55, 75),
        sex="male",
        diagnoses=[
            {"code": "E11.9", "text": "Type 2 Diabetes without complications", "since": "2014"},
            {"code": "I10", "text": "Essential Hypertension", "since": "2016"},
            {"code": "N18.3", "text": "Chronic kidney disease stage 3", "since": "2021"}
        ],
        medications=["metformin", "losartan", "furosemide"],
        a1c_range=(8.5, 10.8),
        condition_focus=["type 2 diabetes", "chronic kidney disease"]
    ),
    PatientArchetype(
        age_range=(35, 55),
        sex="female",
        diagnoses=[
            {"code": "E11.9", "text": "Type 2 Diabetes without complications", "since": "2019"},
            {"code": "E66.9", "text": "Obesity, unspecified", "since": "2018"}
        ],
        medications=["metformin", "semaglutide"],
        a1c_range=(6.8, 8.0),
        condition_focus=["type 2 diabetes", "obesity", "weight management"]
    )
]

RESOURCE_TYPES = [
    "LabReport",
    "ClinicalNote", 
    "DischargeSummary",
    "MedicationList",
    "VitalSigns",
    "RadiologyReport",
    "ReferralNote"
]

class EHRDataGenerator:
    def __init__(self):
        self.fake = Faker()
        self.patients = []
        self.resources = []
        self.derived_facts = []
        
        # Mid-tier American cities that make sense for a diabetes/hypertension clinic
        self.mid_tier_cities = [
            "Springfield, IL", "Madison, WI", "Fort Wayne, IN", "Grand Rapids, MI",
            "Chattanooga, TN", "Spokane, WA", "Boise, ID", "Reno, NV",
            "Lansing, MI", "Peoria, IL", "Cedar Rapids, IA", "Green Bay, WI",
            "Evansville, IN", "Dayton, OH", "Rockford, IL", "Springfield, MO",
            "Fargo, ND", "Sioux Falls, SD", "Burlington, VT", "Manchester, NH"
        ]
    
    def generate_patients(self, num_patients: int) -> List[Dict[str, Any]]:
        """Generate patient profiles using archetypes"""
        patients = []
        
        for i in range(num_patients):
            archetype = self.fake.random_element(PATIENT_ARCHETYPES)
            patient = {
                "id": f"P{(i + 1):03d}",
                "name": self.fake.name(),
                "email": self.fake.email(),
                "consent_given": True,
                "preferences": {
                    "preferred_location": self.fake.random_element(self.mid_tier_cities),
                    "willing_to_travel": self.fake.boolean(),
                    "condition_focus": archetype.condition_focus,
                    "trial_phase_preference": self.fake.random_sample(
                        ["Phase I", "Phase II", "Phase III"], length=self.fake.random_int(1, 2)
                    ),
                    "trial_type": self.fake.random_sample(
                        ["drug", "observational", "behavioral"], length=self.fake.random_int(1, 2)
                    )
                },
                "created_at": self.fake.date_time_between(start_date="-1y").isoformat(),
                "_archetype": archetype  # Internal use
            }
            patients.append(patient)
        
        self.patients = patients
        return patients
    
    def generate_lab_report(self, patient_id: str, archetype: PatientArchetype) -> str:
        """Generate realistic lab report content"""
        a1c = round(self.fake.random.uniform(*archetype.a1c_range), 1)
        glucose = self.fake.random_int(140, 220)
        creatinine = round(self.fake.random.uniform(0.8, 1.2), 1)
        egfr = self.fake.random_int(75, 105)
        ldl = self.fake.random_int(100, 150)
        hdl = self.fake.random_int(40, 60) if archetype.sex == "female" else self.fake.random_int(35, 55)
        triglycerides = self.fake.random_int(150, 220)
        
        return f"""Laboratory Results - {self.fake.date_between(start_date='-30d').strftime('%m/%d/%Y')}
        
Hemoglobin A1C: {a1c}% (ref <5.7%)
Fasting Glucose: {glucose} mg/dL (ref 70-99 mg/dL)
Creatinine: {creatinine} mg/dL (ref 0.6-1.2 mg/dL)
eGFR: {egfr} mL/min/1.73 m²
Lipid Panel:
  - LDL Cholesterol: {ldl} mg/dL
  - HDL Cholesterol: {hdl} mg/dL  
  - Triglycerides: {triglycerides} mg/dL
Microalbumin/Creatinine Ratio: {round(self.fake.random.uniform(15, 45), 1)} mg/g"""
    
    def generate_clinical_note(self, patient_id: str, archetype: PatientArchetype) -> str:
        """Generate clinical visit note"""
        age = self.fake.random_int(*archetype.age_range)
        weight = self.fake.random_int(70, 95)
        bmi = round(self.fake.random.uniform(28, 35), 1)
        sbp = self.fake.random_int(135, 155)
        dbp = self.fake.random_int(85, 95)
        a1c = round(self.fake.random.uniform(*archetype.a1c_range), 1)
        
        return f"""Clinical Visit Note - {self.fake.date_between(start_date='-60d').strftime('%m/%d/%Y')}

{age}-year-old {archetype.sex} with history of {', '.join([d['text'] for d in archetype.diagnoses])}.

Current medications: {', '.join([f"{med} {'1000mg BID' if med == 'metformin' else '10mg daily'}" for med in archetype.medications])}.

Vital Signs:
- Blood Pressure: {sbp}/{dbp} mmHg
- Weight: {weight} kg
- BMI: {bmi}

Assessment: Patient continues to have suboptimal glycemic control with A1C of {a1c}%. 
Blood pressure remains elevated despite current antihypertensive therapy.

Plan:
- Continue current diabetes medications
- Reinforce dietary counseling and exercise recommendations  
- Consider medication adjustment if A1C remains >8% at next visit
- Recheck labs in 12 weeks
- Ophthalmology referral for diabetic retinal screening"""
    
    def generate_discharge_summary(self, patient_id: str, archetype: PatientArchetype) -> str:
        """Generate hospital discharge summary"""
        admission_reasons = [
            "hypoglycemia episode",
            "diabetic ketoacidosis", 
            "hypertensive urgency",
            "chest pain evaluation"
        ]
        reason = self.fake.random_element(admission_reasons)
        glucose = self.fake.random_int(55, 75)
        
        return f"""Hospital Discharge Summary - {self.fake.date_between(start_date='-90d').strftime('%m/%d/%Y')}

Admission Diagnosis: {reason}
Discharge Diagnosis: {reason}, resolved

Hospital Course: 
Patient presented to ED with {reason}. Glucose level was {glucose} mg/dL on arrival.
Treated with oral glucose and IV dextrose with good response. Blood sugar normalized within 2 hours.

Medications at Discharge: {', '.join(archetype.medications)} - no changes made

Discharge Instructions:
- Follow up with primary care provider in 1-2 weeks
- Continue current medications as prescribed
- Blood glucose monitoring 2x daily
- Return to ED if symptoms recur"""
    
    def generate_medication_list(self, patient_id: str, archetype: PatientArchetype) -> str:
        """Generate current medication list"""
        med_doses = ["5mg", "10mg", "20mg"]
        
        med_list = [
            "1. Metformin 1000 mg PO BID - for diabetes",
            f"2. {archetype.medications[1]} {self.fake.random_element(med_doses)} PO daily - for hypertension"
        ]
        
        if len(archetype.medications) > 2:
            med_list.append(f"3. {archetype.medications[2]} 20 mg PO QHS - for hyperlipidemia")
        
        return f"""Current Medication List - Updated {self.fake.date_between(start_date='-14d').strftime('%m/%d/%Y')}

Active Medications:
{chr(10).join(med_list)}

Allergies: NKDA (No Known Drug Allergies)

Adherence: Patient reports good adherence, occasionally misses evening doses
Last pharmacy refill: {self.fake.date_between(start_date='-20d').strftime('%m/%d/%Y')}"""
    
    def generate_ai_summary(self, resource_type: str, content: str) -> str:
        """Generate AI summary based on resource type"""
        summaries = {
            "LabReport": [
                "Poor glycemic control indicated by elevated A1C; lipid management needed.",
                "Diabetes well-controlled; renal function stable for continued metformin use.",
                "Suboptimal glucose control; consider medication intensification."
            ],
            "ClinicalNote": [
                "Diabetes and hypertension with elevated BP; lifestyle counseling reinforced.",
                "Stable chronic conditions; medication adherence good; routine follow-up planned.",
                "Multiple comorbidities requiring ongoing management and monitoring."
            ],
            "DischargeSummary": [
                "Hypoglycemia episode resolved; patient education provided on prevention.",
                "Brief hospitalization for diabetes-related complication; stable at discharge.",
                "Routine discharge after successful management of acute episode."
            ],
            "MedicationList": [
                "Standard diabetes and hypertension regimen; adherence generally acceptable.",
                "Current medications appropriate for comorbidities; no immediate changes needed.",
                "Multi-drug regimen for diabetes management; monitoring for drug interactions."
            ]
        }
        
        return self.fake.random_element(summaries.get(resource_type, ["Standard clinical documentation reviewed."]))
    
    def generate_ehr_resources(
        self, 
        patients: List[Dict[str, Any]], 
        min_resources: int = 3, 
        max_resources: int = 6
    ) -> List[Dict[str, Any]]:
        """Generate EHR resources for patients"""
        resources = []
        
        for patient in patients:
            archetype = patient["_archetype"]
            num_resources = self.fake.random_int(min_resources, max_resources)
            
            for i in range(num_resources):
                resource_type = self.fake.random_element(RESOURCE_TYPES)
                created_time = self.fake.date_time_between(start_date="-1y")
                fetch_time = created_time + timedelta(
                    milliseconds=self.fake.random_int(1000, 10000)
                )
                processing_time = fetch_time + timedelta(
                    milliseconds=self.fake.random_int(5000, 60000)
                )
                
                # Generate content based on resource type
                if resource_type == "LabReport":
                    content = self.generate_lab_report(patient["id"], archetype)
                elif resource_type == "ClinicalNote":
                    content = self.generate_clinical_note(patient["id"], archetype)
                elif resource_type == "DischargeSummary":
                    content = self.generate_discharge_summary(patient["id"], archetype)
                elif resource_type == "MedicationList":
                    content = self.generate_medication_list(patient["id"], archetype)
                else:
                    content = f"{resource_type} document for patient {patient['id']}"
                
                # Weighted state selection
                state_weights = [
                    (ProcessingState.PROCESSING_STATE_COMPLETED, 0.7),
                    (ProcessingState.PROCESSING_STATE_PROCESSING, 0.15),
                    (ProcessingState.PROCESSING_STATE_FAILED, 0.1),
                    (ProcessingState.PROCESSING_STATE_NOT_STARTED, 0.05)
                ]
                rand_val = self.fake.random.random()
                cumulative = 0
                state = ProcessingState.PROCESSING_STATE_COMPLETED  # default
                for s, weight in state_weights:
                    cumulative += weight
                    if rand_val <= cumulative:
                        state = s
                        break
                
                resource = {
                    "metadata": {
                        "state": state.value,
                        "created_time": created_time.isoformat(),
                        "fetch_time": fetch_time.isoformat(),
                        "processed_time": processing_time.isoformat() if state == ProcessingState.PROCESSING_STATE_COMPLETED else None,
                        "identifier": {
                            "key": f"res_{patient['id']}_{(i + 1):04d}",
                            "uid": f"{hash(patient['id']) % 10000 + i + 1:04d}",
                            "patient_id": patient["id"]
                        },
                        "resource_type": resource_type,
                        "version": self.fake.random_element([
                            FHIRVersion.FHIR_VERSION_R4.value,
                            FHIRVersion.FHIR_VERSION_R4B.value
                        ])
                    },
                    "human_readable_str": content,
                    "ai_summary": self.generate_ai_summary(resource_type, content) if state == ProcessingState.PROCESSING_STATE_COMPLETED else None
                }
                
                resources.append(resource)
        
        self.resources = resources
        return resources
    
    def generate_derived_facts(self, patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate derived clinical facts for trial matching"""
        facts = []
        
        for patient in patients:
            archetype = patient["_archetype"]
            
            fact = {
                "patient_id": patient["id"],
                "age_years": self.fake.random_int(*archetype.age_range),
                "sex": archetype.sex,
                "diagnoses": archetype.diagnoses,
                "medications": archetype.medications,
                "key_labs": {
                    "a1c": round(self.fake.random.uniform(*archetype.a1c_range), 1),
                    "egfr": self.fake.random_int(75, 105),
                    "ldl": self.fake.random_int(100, 150),
                    "sbp": self.fake.random_int(135, 155),
                    "dbp": self.fake.random_int(85, 95)
                },
                "exclusions": self.fake.random_sample(
                    ["pregnancy", "type1_diabetes", "severe_renal_disease"], 
                    length=self.fake.random_int(0, 1)
                ),
                "location": self.fake.zipcode(),
                "extracted_at": datetime.now().isoformat()
            }
            
            facts.append(fact)
        
        self.derived_facts = facts
        return facts
    
    def generate_complete_dataset(
        self, 
        num_patients: int = 3, 
        min_resources: int = 3, 
        max_resources: int = 6
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate complete dataset with patients, resources, and derived facts"""
        patients = self.generate_patients(num_patients)
        resources = self.generate_ehr_resources(patients, min_resources, max_resources)
        derived_facts = self.generate_derived_facts(patients)
        
        # Clean archetypes from patient data for serialization
        for patient in patients:
            if "_archetype" in patient:
                del patient["_archetype"]
        
        return {
            "patients": patients,
            "resources": resources,
            "derived_facts": derived_facts
        }
