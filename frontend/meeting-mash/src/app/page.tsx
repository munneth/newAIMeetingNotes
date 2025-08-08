import Image from "next/image";
import Link from "next/link";
import NavbarProd from "@/components/navbarProd";
import MeetingAdd from "@/components/meeting-add";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <NavbarProd />
      <div className="flex-1 flex items-center justify-center">
        <MeetingAdd />
      </div>
    </div>
  );
}
