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
    const body = await request.json()
    const { meetingId, startTime, duration } = body
    
    if (!meetingId || !startTime) {
      return NextResponse.json({ error: 'Meeting ID and start time are required' }, { status: 400 })
    }

    // Check if meeting is upcoming (within next 1 hour)
    const meetingTime = new Date(startTime)
    const now = new Date()
    const timeDiff = meetingTime.getTime() - now.getTime()
    const hoursDiff = timeDiff / (1000 * 60 * 60)
    
    if (hoursDiff > 1) {
      return NextResponse.json({ 
        message: 'Meeting is not upcoming (more than 1 hour away)',
        scheduled: false 
      })
    }

    // Get meeting details
    const meeting = await prisma.meeting.findFirst({
      where: {
        id: meetingId,
        userId: session.user.id
      }
    })
    
    if (!meeting) {
      return NextResponse.json({ error: 'Meeting not found' }, { status: 404 })
    }

    // Prepare meeting data for bot
    const meetingData = {
      link: meeting.link,
      meetingId: meeting.meetingId,
      start_time: startTime,
      duration: duration || meeting.duration || "60",
      title: `Meeting for ${session.user.email}`
    }

    // Call bot orchestrator to create instance
    const orchestratorUrl = process.env.BOT_ORCHESTRATOR_URL || 'http://bot-orchestrator-service:8080'
    
    const botResponse = await fetch(`${orchestratorUrl}/create-instance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: session.user.id,
        meeting_id: meetingId,
        meeting_data: meetingData
      })
    })

    if (!botResponse.ok) {
      throw new Error(`Bot orchestrator error: ${botResponse.statusText}`)
    }

    const botResult = await botResponse.json()

    return NextResponse.json({ 
      success: true, 
      instance_id: botResult.instance_id,
      message: 'Bot instance created successfully',
      scheduled: true
    })

  } catch (error) {
    console.error('Error creating bot instance:', error)
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const session = await auth()
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Get user's active bot instances
    const orchestratorUrl = process.env.BOT_ORCHESTRATOR_URL || 'http://bot-orchestrator-service:8080'
    
    const botResponse = await fetch(`${orchestratorUrl}/user-instances/${session.user.id}`)
    
    if (!botResponse.ok) {
      throw new Error(`Bot orchestrator error: ${botResponse.statusText}`)
    }

    const instances = await botResponse.json()

    return NextResponse.json({ instances })

  } catch (error) {
    console.error('Error fetching bot instances:', error)
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    )
  }
}
