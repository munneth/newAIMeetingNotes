import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'
import { auth } from '@/lib/auth'

const prisma = new PrismaClient()

export async function POST(request: NextRequest) {
  try {
    // Get the current user session
    const session = await auth()
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Parse the request body
    const { link, duration } = await request.json()

    // Validate required fields
    if (!link) {
      return NextResponse.json({ error: 'Meeting link is required' }, { status: 400 })
    }

    // Create the meeting in the database
    const meeting = await prisma.meeting.create({
      data: {
        link,
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