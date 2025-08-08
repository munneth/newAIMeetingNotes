"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function MeetingAdd() {
  const [durationVisible, setDurationVisible] = useState(false);
  const [link, setLink] = useState("");
  const [duration, setDuration] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleDurationClick = () => {
    if (link.trim()) {
      setDurationVisible(true);
    } else {
      alert("Please enter a meeting link");
    }
  };

  const handleSubmit = async () => {
    if (!link.trim()) {
      alert("Please enter a meeting link");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/meetings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          link: link.trim(),
          duration: duration.trim() || null,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        alert("Meeting added successfully!");
        setLink("");
        setDuration("");
        setDurationVisible(false);
      } else {
        alert(data.error || "Failed to add meeting");
      }
    } catch (error) {
      console.error('Error submitting meeting:', error);
      alert("An error occurred while adding the meeting");
    } finally {
      setIsSubmitting(false);
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
          <Button 
            onClick={handleSubmit} 
            className="w-32"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Saving..." : "Done"}
          </Button>
        </div>
      )}
    </div>
  );
}
