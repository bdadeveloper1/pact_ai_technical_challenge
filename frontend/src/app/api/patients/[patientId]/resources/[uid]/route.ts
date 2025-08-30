import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { patientId: string; uid: string } }
) {
  try {
    const { patientId, uid } = params;
    
    // Get all resources for patient and find the specific one by UID
    const response = await fetch(`${BACKEND_URL}/api/resources?patient_id=${patientId}`);
    const data = await response.json();
    
    const resource = data.resources?.find((r: any) => r.metadata.identifier.uid === uid);
    
    if (!resource) {
      return NextResponse.json({ error: 'Resource not found' }, { status: 404 });
    }
    
    return NextResponse.json(resource);
  } catch (error) {
    console.error('Failed to fetch resource detail:', error);
    return NextResponse.json({ error: 'Failed to fetch resource detail' }, { status: 500 });
  }
}
