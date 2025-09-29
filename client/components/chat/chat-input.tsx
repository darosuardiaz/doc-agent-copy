"use client"

import { useState, type KeyboardEvent } from "react"
import { Send, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ onSendMessage, disabled, placeholder = "Type your message..." }: ChatInputProps) {
  const [message, setMessage] = useState("")

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage("")
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex items-center gap-2 p-4 border-t bg-background">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="h-10 resize-none"
      />
      <Button onClick={handleSend} disabled={!message.trim() || disabled} size="lg" className="px-4">
        {disabled ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
      </Button>
    </div>
  )
}
