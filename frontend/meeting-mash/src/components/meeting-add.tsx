import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function MeetingAdd() {
    return (
        <div className="text-center space-y-6">
            <h1 className="text-2xl font-bold">Enter your meeting link</h1>
            <div className="flex flex-col items-center space-y-4">
                <Input type="email" placeholder="Email" className="w-64 text-center"/>
                <Button className="w-32">Add</Button>
            </div>
        </div>
    )
}