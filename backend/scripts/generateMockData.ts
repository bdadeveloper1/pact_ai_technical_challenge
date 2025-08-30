import { faker } from '@faker-js/faker';
import { writeFileSync } from 'fs';
import { join } from 'path';
import {
  EHRResourceJson,
  PatientProfile,
  DerivedClinicalFacts,
  ProcessingState,
  FHIRVersion,
  RESOURCE_TYPES
} from '../src/lib/types';

// Patient archetypes for diabetes/hypertension use case
const PATIENT_ARCHETYPES = [
  {
    ageRange: [45, 65],
    sex: 'female' as const,
    diagnoses: [
      { code: 'E11.9', text: 'Type 2 Diabetes without complications', since: '2017' },
      { code: 'I10', text: 'Essential Hypertension', since: '2019' }
    ],
    medications: ['metformin', 'lisinopril'],
    a1c: faker.number.float({ min: 7.8, max: 9.2, precision: 0.1 }),
    conditionFocus: ['type 2 diabetes', 'hypertension']
  },
  {
    ageRange: [50, 70],
    sex: 'male' as const,
    diagnoses: [
      { code: 'E11.9', text: 'Type 2 Diabetes without complications', since: '2015' },
      { code: 'I10', text: 'Essential Hypertension', since: '2018' },
      { code: 'E78.5', text: 'Hyperlipidemia', since: '2020' }
    ],
    medications: ['metformin', 'amlodipine', 'atorvastatin'],
    a1c: faker.number.float({ min: 8.0, max: 10.1, precision: 0.1 }),
    conditionFocus: ['type 2 diabetes', 'cardiovascular disease']
  },
  {
    ageRange: [40, 60],
    sex: 'female' as const,
    diagnoses: [
      { code: 'E11.9', text: 'Type 2 Diabetes without complications', since: '2020' }
    ],
    medications: ['metformin', 'glipizide'],
    a1c: faker.number.float({ min: 7.2, max: 8.5, precision: 0.1 }),
    conditionFocus: ['type 2 diabetes']
  }
];

function generatePatientProfiles(): PatientProfile[] {
  return PATIENT_ARCHETYPES.map((archetype, index) => ({
    id: `P${(index + 1).toString().padStart(3, '0')}`,
    name: faker.person.fullName(),
    email: faker.internet.email(),
    consentGiven: true,
    preferences: {
      preferredLocation: faker.location.city(),
      willingToTravel: faker.datatype.boolean(),
      conditionFocus: archetype.conditionFocus,
      trialPhasePreference: faker.helpers.arrayElements(['Phase I', 'Phase II', 'Phase III'], { min: 1, max: 2 }),
      trialType: faker.helpers.arrayElements(['drug', 'observational', 'behavioral'], { min: 1, max: 2 })
    },
    createdAt: faker.date.past({ years: 1 }).toISOString()
  }));
}

function generateLabReport(patientId: string, archetype: typeof PATIENT_ARCHETYPES[0]): string {
  const glucose = faker.number.int({ min: 140, max: 220 });
  const creatinine = faker.number.float({ min: 0.8, max: 1.2, precision: 0.1 });
  const eGFR = faker.number.int({ min: 75, max: 105 });
  const ldl = faker.number.int({ min: 100, max: 150 });
  const hdl = archetype.sex === 'female' ? faker.number.int({ min: 40, max: 60 }) : faker.number.int({ min: 35, max: 55 });
  const triglycerides = faker.number.int({ min: 150, max: 220 });
  
  return `Laboratory Results - ${faker.date.recent({ days: 30 }).toLocaleDateString()}
  
Hemoglobin A1C: ${archetype.a1c}% (ref <5.7%)
Fasting Glucose: ${glucose} mg/dL (ref 70-99 mg/dL)
Creatinine: ${creatinine} mg/dL (ref 0.6-1.2 mg/dL)
eGFR: ${eGFR} mL/min/1.73 m²
Lipid Panel:
  - LDL Cholesterol: ${ldl} mg/dL
  - HDL Cholesterol: ${hdl} mg/dL  
  - Triglycerides: ${triglycerides} mg/dL
Microalbumin/Creatinine Ratio: ${faker.number.float({ min: 15, max: 45, precision: 1 })} mg/g`;
}

function generateClinicalNote(patientId: string, archetype: typeof PATIENT_ARCHETYPES[0]): string {
  const age = faker.number.int({ min: archetype.ageRange[0], max: archetype.ageRange[1] });
  const weight = faker.number.int({ min: 70, max: 95 });
  const bmi = faker.number.float({ min: 28, max: 35, precision: 0.1 });
  const sbp = faker.number.int({ min: 135, max: 155 });
  const dbp = faker.number.int({ min: 85, max: 95 });
  
  return `Clinical Visit Note - ${faker.date.recent({ days: 60 }).toLocaleDateString()}

${age}-year-old ${archetype.sex} with history of ${archetype.diagnoses.map(d => d.text).join(', ')}.

Current medications: ${archetype.medications.join(' 1000mg BID, ')} 10mg daily.

Vital Signs:
- Blood Pressure: ${sbp}/${dbp} mmHg
- Weight: ${weight} kg
- BMI: ${bmi}

Assessment: Patient continues to have suboptimal glycemic control with A1C of ${archetype.a1c}%. 
Blood pressure remains elevated despite current antihypertensive therapy.

Plan:
- Continue current diabetes medications
- Reinforce dietary counseling and exercise recommendations  
- Consider medication adjustment if A1C remains >8% at next visit
- Recheck labs in 12 weeks
- Ophthalmology referral for diabetic retinal screening`;
}

function generateDischargeSummary(patientId: string, archetype: typeof PATIENT_ARCHETYPES[0]): string {
  const admissionReason = faker.helpers.arrayElement([
    'hypoglycemia episode',
    'diabetic ketoacidosis', 
    'hypertensive urgency',
    'chest pain evaluation'
  ]);
  
  return `Hospital Discharge Summary - ${faker.date.recent({ days: 90 }).toLocaleDateString()}

Admission Diagnosis: ${admissionReason}
Discharge Diagnosis: ${admissionReason}, resolved

Hospital Course: 
Patient presented to ED with ${admissionReason}. Glucose level was ${faker.number.int({ min: 55, max: 75 })} mg/dL on arrival.
Treated with oral glucose and IV dextrose with good response. Blood sugar normalized within 2 hours.

Medications at Discharge: ${archetype.medications.join(', ')} - no changes made

Discharge Instructions:
- Follow up with primary care provider in 1-2 weeks
- Continue current medications as prescribed
- Blood glucose monitoring 2x daily
- Return to ED if symptoms recur`;
}

function generateMedicationList(patientId: string, archetype: typeof PATIENT_ARCHETYPES[0]): string {
  return `Current Medication List - Updated ${faker.date.recent({ days: 14 }).toLocaleDateString()}

Active Medications:
1. Metformin 1000 mg PO BID - for diabetes
2. ${archetype.medications[1]} ${faker.helpers.arrayElement(['5mg', '10mg', '20mg'])} PO daily - for hypertension
${archetype.medications.length > 2 ? `3. ${archetype.medications[2]} 20 mg PO QHS - for hyperlipidemia` : ''}

Allergies: NKDA (No Known Drug Allergies)

Adherence: Patient reports good adherence, occasionally misses evening doses
Last pharmacy refill: ${faker.date.recent({ days: 20 }).toLocaleDateString()}`;
}

function generateAISummary(resourceType: string, humanReadable: string): string {
  const summaries = {
    LabReport: [
      "Poor glycemic control indicated by elevated A1C; lipid management needed.",
      "Diabetes well-controlled; renal function stable for continued metformin use.",
      "Suboptimal glucose control; consider medication intensification."
    ],
    ClinicalNote: [
      "Diabetes and hypertension with elevated BP; lifestyle counseling reinforced.",
      "Stable chronic conditions; medication adherence good; routine follow-up planned.",
      "Multiple comorbidities requiring ongoing management and monitoring."
    ],
    DischargeSummary: [
      "Hypoglycemia episode resolved; patient education provided on prevention.",
      "Brief hospitalization for diabetes-related complication; stable at discharge.",
      "Routine discharge after successful management of acute episode."
    ],
    MedicationList: [
      "Standard diabetes and hypertension regimen; adherence generally acceptable.",
      "Current medications appropriate for comorbidities; no immediate changes needed.",
      "Multi-drug regimen for diabetes management; monitoring for drug interactions."
    ]
  };
  
  return faker.helpers.arrayElement(summaries[resourceType as keyof typeof summaries] || ["Standard clinical documentation reviewed."]);
}

function generateEHRResources(): EHRResourceJson[] {
  const patients = generatePatientProfiles();
  const resources: EHRResourceJson[] = [];
  
  patients.forEach((patient, patientIndex) => {
    const archetype = PATIENT_ARCHETYPES[patientIndex];
    const numResources = faker.number.int({ min: 3, max: 6 });
    
    for (let i = 0; i < numResources; i++) {
      const resourceType = faker.helpers.arrayElement(RESOURCE_TYPES);
      const createdTime = faker.date.past({ years: 1 });
      const fetchTime = new Date(createdTime.getTime() + faker.number.int({ min: 1000, max: 10000 }));
      const processingTime = new Date(fetchTime.getTime() + faker.number.int({ min: 5000, max: 60000 }));
      
      let humanReadableStr = '';
      switch (resourceType) {
        case 'LabReport':
          humanReadableStr = generateLabReport(patient.id, archetype);
          break;
        case 'ClinicalNote':
          humanReadableStr = generateClinicalNote(patient.id, archetype);
          break;
        case 'DischargeSummary':
          humanReadableStr = generateDischargeSummary(patient.id, archetype);
          break;
        case 'MedicationList':
          humanReadableStr = generateMedicationList(patient.id, archetype);
          break;
        default:
          humanReadableStr = `${resourceType} document for patient ${patient.id}`;
      }
      
      const state = faker.helpers.weightedArrayElement([
        { weight: 70, value: ProcessingState.PROCESSING_STATE_COMPLETED },
        { weight: 15, value: ProcessingState.PROCESSING_STATE_PROCESSING },
        { weight: 10, value: ProcessingState.PROCESSING_STATE_FAILED },
        { weight: 5, value: ProcessingState.PROCESSING_STATE_NOT_STARTED }
      ]);
      
      resources.push({
        metadata: {
          state,
          createdTime: createdTime.toISOString(),
          fetchTime: fetchTime.toISOString(),
          processedTime: state === ProcessingState.PROCESSING_STATE_COMPLETED ? processingTime.toISOString() : undefined,
          identifier: {
            key: `res_${patient.id}_${(i + 1).toString().padStart(4, '0')}`,
            uid: (patientIndex * 1000 + i + 1).toString().padStart(4, '0'),
            patientId: patient.id
          },
          resourceType,
          version: faker.helpers.arrayElement([FHIRVersion.FHIR_VERSION_R4, FHIRVersion.FHIR_VERSION_R4B])
        },
        humanReadableStr,
        aiSummary: state === ProcessingState.PROCESSING_STATE_COMPLETED ? generateAISummary(resourceType, humanReadableStr) : undefined
      });
    }
  });
  
  return resources;
}

function generateDerivedFacts(): DerivedClinicalFacts[] {
  const patients = generatePatientProfiles();
  
  return patients.map((patient, index) => {
    const archetype = PATIENT_ARCHETYPES[index];
    return {
      patientId: patient.id,
      ageYears: faker.number.int({ min: archetype.ageRange[0], max: archetype.ageRange[1] }),
      sex: archetype.sex,
      diagnoses: archetype.diagnoses,
      medications: archetype.medications,
      keyLabs: {
        a1c: archetype.a1c,
        eGFR: faker.number.int({ min: 75, max: 105 }),
        ldl: faker.number.int({ min: 100, max: 150 }),
        sbp: faker.number.int({ min: 135, max: 155 }),
        dbp: faker.number.int({ min: 85, max: 95 })
      },
      exclusions: faker.helpers.arrayElements(['pregnancy', 'type1_diabetes', 'severe_renal_disease'], { min: 0, max: 1 }),
      location: faker.location.zipCode(),
      extractedAt: new Date().toISOString()
    };
  });
}

// Generate all mock data
function main() {
  console.log('Generating mock EHR data...');
  
  const patients = generatePatientProfiles();
  const resources = generateEHRResources();
  const derivedFacts = generateDerivedFacts();
  
  // Write to JSON files
  writeFileSync(
    join(__dirname, '../src/data/mockPatients.json'),
    JSON.stringify(patients, null, 2)
  );
  
  writeFileSync(
    join(__dirname, '../src/data/mockResources.json'),
    JSON.stringify(resources, null, 2)
  );
  
  writeFileSync(
    join(__dirname, '../src/data/mockDerivedFacts.json'),
    JSON.stringify(derivedFacts, null, 2)
  );
  
  console.log(`Generated ${patients.length} patients with ${resources.length} EHR resources`);
  console.log('Files written to src/data/');
}

main();
