"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function MeetingAdd() {
  const [durationVisible, setDurationVisible] = useState(false);
  const handleDurationClick = () => {
    setDurationVisible(!durationVisible);
    console.log("durationVisible: ", durationVisible);
  };
  return (
    <div className="text-center space-y-6">
      <h1 className="text-2xl font-bold">Enter your meeting link</h1>
      <div className="flex flex-col items-center space-y-4">
        <Input placeholder="Link" className="w-64 text-center" />
        <Button onClick={handleDurationClick} className="w-32">
          Add
        </Button>
      </div>
      {durationVisible && (
        <div className="flex flex-col items-center space-y-4">
          <h1 className="text-2xl font-bold">Estimated Meeting Duration</h1>
          <Input placeholder="Duration" className="w-64 text-center" />
          <Button onClick={handleDurationClick} className="w-32">
            Done
          </Button>
        </div>
      )}
    </div>
  );
}
