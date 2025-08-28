"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function MeetingAdd() {
  const [durationVisible, setDurationVisible] = useState(false);
  const [link, setLink] = useState("");
  const [meetingId, setMeetingId] = useState("");
  const [duration, setDuration] = useState("");
  const [startTime, setStartTime] = useState("");

  const handleDurationClick = () => {
    setDurationVisible(!durationVisible);
    console.log("durationVisible: ", durationVisible);
  };

  const handleSubmit = async () => {
    console.log("submit");
    
    // First, save the meeting
    const response = await fetch("/api/meetings", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        link: link,
        meetingId: meetingId,
        duration: duration,
      }),
    });
    const data = await response.json();
    
    if (data.success) {
      // If meeting was saved successfully, try to create bot instance
      if (startTime) {
        try {
          const botResponse = await fetch("/api/bot-instances", {
            method: "POST",
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              meetingId: data.meeting.id,
              startTime: startTime,
              duration: duration,
            }),
          });
          
          const botData = await botResponse.json();
          
          if (botData.scheduled) {
            alert(`Meeting added successfully! Bot will join ${startTime}`);
          } else {
            alert(`Meeting added successfully! ${botData.message}`);
          }
        } catch (error) {
          console.error("Bot creation failed:", error);
          alert("Meeting added successfully, but bot creation failed");
        }
      } else {
        alert("Meeting added successfully!");
      }
    } else {
      alert("Failed to add meeting");
    }
  };

  return (
    <div className="text-center space-y-6">
      <h1 className="text-2xl font-bold">Enter your meeting link</h1>
      <div className="flex flex-col items-center space-y-4">
        <Input 
          placeholder="Link" 
          className="w-64 text-center"
          value={link}
          onChange={(e) => setLink(e.target.value)}
        />
        <Input 
          placeholder="Meeting ID" 
          className="w-64 text-center"
          value={meetingId}
          onChange={(e) => setMeetingId(e.target.value)}
        />
        <Input 
          type="datetime-local"
          className="w-64 text-center"
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
        />

        <Button onClick={handleDurationClick} className="w-32">
          Add
        </Button>
      </div>
      {durationVisible && (
        <div className="flex flex-col items-center space-y-4">
          <h1 className="text-2xl font-bold">Estimated Meeting Duration</h1>
          <Input 
            placeholder="Duration" 
            className="w-64 text-center"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
          />
          <Button onClick={handleSubmit} className="w-32">
            Done
          </Button>
        </div>
      )}
    </div>
  );
}
