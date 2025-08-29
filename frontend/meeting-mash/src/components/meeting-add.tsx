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
    console.log("startTime value:", startTime);
    
    // Format the time for database storage (HH:MM:SS format)
    const formattedTime = startTime ? `${startTime}:00` : null;
    console.log("formattedTime:", formattedTime);
    
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
        startTime: formattedTime,
      }),
    });
    const data = await response.json();
    
    if (data.success) {
      // Meeting saved successfully - orchestrator will automatically detect and schedule the bot
      if (startTime) {
        alert(`Meeting added successfully! Bot will automatically join at ${startTime}`);
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
        <div className="flex flex-col items-center space-y-2">
          <label className="text-sm font-medium">Meeting Start Time</label>
          <Input 
            type="time"
            placeholder="Select time"
            className="w-64 text-center"
            value={startTime}
            onChange={(e) => {
              console.log("Time input changed:", e.target.value);
              setStartTime(e.target.value);
            }}
          />
        </div>

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
