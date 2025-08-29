import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function GET(request: NextRequest) {
  try {
    // Check for API key authentication
    const apiKey = request.headers.get('authorization')?.replace('Bearer ', '')
    
    if (!apiKey || apiKey !== process.env.ORCHESTRATOR_API_KEY) {
      return NextResponse.json({ error: 'Unauthorized - Invalid API key' }, { status: 401 })
    }
    
    // Get all meetings (authenticated orchestrator access)
    const meetings = await prisma.meeting.findMany({
      orderBy: {
        createdAt: 'desc',
      },
    })
    return NextResponse.json({ meetings })
  } catch (error) {
    console.error('Error fetching meetings for orchestrator:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

