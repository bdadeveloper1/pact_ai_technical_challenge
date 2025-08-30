import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { patientId: string } }
) {
  try {
    const { patientId } = params;
    const url = new URL(request.url);
    const searchParams = url.searchParams;
    
    // Forward query parameters to backend
    const backendUrl = new URL(`${BACKEND_URL}/api/resources`);
    backendUrl.searchParams.set('patient_id', patientId);
    
    // Forward other params (limit, offset, etc.)
    for (const [key, value] of searchParams.entries()) {
      if (key !== 'patientId') {
        backendUrl.searchParams.set(key, value);
      }
    }

    const response = await fetch(backendUrl.toString());
    const data = await response.json();
    
    // Return just the resources array for cleaner frontend API
    return NextResponse.json(data.resources || []);
  } catch (error) {
    console.error('Failed to fetch patient resources:', error);
    return NextResponse.json({ error: 'Failed to fetch patient resources' }, { status: 500 });
  }
}
