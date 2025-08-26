import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'
import { auth } from '@/lib/auth'

const prisma = new PrismaClient()

export async function POST(request: NextRequest) {
  try {
    // Get the current user session
    const session = await auth()
    
    console.log('Session:', session) // Debug log
    
    if (!session) {
      return NextResponse.json({ error: 'No session found' }, { status: 401 })
    }
    
    if (!session.user) {
      return NextResponse.json({ error: 'No user in session' }, { status: 401 })
    }
    
    if (!session.user.id) {
      return NextResponse.json({ error: 'No user ID in session' }, { status: 401 })
    }

    // Parse the request body
    const body = await request.json()
    const { link, meetingId, duration } = body
    
    console.log('Request body:', body)
    console.log('Extracted meetingId:', meetingId)

    // Validate required fields
    if (!link) {
      return NextResponse.json({ error: 'Meeting link is required' }, { status: 400 })
    }

    // Check if user exists in database
    const user = await prisma.user.findUnique({
      where: { id: session.user.id }
    })
    
    console.log('User ID from session:', session.user.id)
    console.log('User found in database:', user)
    
    if (!user) {
      return NextResponse.json({ error: 'User not found in database' }, { status: 404 })
    }

    // Create the meeting in the database
    const meeting = await prisma.meeting.create({
      data: {
        link,
        meetingId: meetingId || null,
        duration: duration || null,
        userId: session.user.id,
      },
    })

    return NextResponse.json({ 
      success: true, 
      meeting 
    }, { status: 201 })

  } catch (error) {
    console.error('Error creating meeting:', error)
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    const session = await auth()
    
    console.log('GET Session:', session) // Debug log
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Get all meetings for the current user
    const meetings = await prisma.meeting.findMany({
      where: {
        userId: session.user.id,
      },
      orderBy: {
        createdAt: 'desc',
      },
    })

    return NextResponse.json({ meetings })

  } catch (error) {
    console.error('Error fetching meetings:', error)
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    )
  }
} 