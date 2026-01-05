'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function SettingsPage() {
    const [apiKeys, setApiKeys] = useState({
        openai: '',
        anthropic: '',
        google: ''
    })

    const [notifications, setNotifications] = useState({
        email: true,
        telegram: false,
        discord: false
    })

    return (
        <div className="space-y-6 max-w-4xl">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Settings</h1>
                <p className="text-muted-foreground">Configure your prediction preferences</p>
            </div>

            {/* API Keys */}
            <Card className="bg-card/50">
                <CardHeader>
                    <CardTitle>API Keys</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="openai">OpenAI API Key</Label>
                        <Input
                            id="openai"
                            type="password"
                            placeholder="sk-..."
                            value={apiKeys.openai}
                            onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="anthropic">Anthropic API Key</Label>
                        <Input
                            id="anthropic"
                            type="password"
                            placeholder="sk-ant-..."
                            value={apiKeys.anthropic}
                            onChange={(e) => setApiKeys({ ...apiKeys, anthropic: e.target.value })}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="google">Google API Key</Label>
                        <Input
                            id="google"
                            type="password"
                            placeholder="AIza..."
                            value={apiKeys.google}
                            onChange={(e) => setApiKeys({ ...apiKeys, google: e.target.value })}
                        />
                    </div>
                    <Button>Save API Keys</Button>
                </CardContent>
            </Card>

            {/* Notifications */}
            <Card className="bg-card/50">
                <CardHeader>
                    <CardTitle>Notifications</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="font-medium">Email Notifications</div>
                            <div className="text-sm text-muted-foreground">Receive prediction alerts via email</div>
                        </div>
                        <Button
                            variant={notifications.email ? 'default' : 'outline'}
                            onClick={() => setNotifications({ ...notifications, email: !notifications.email })}
                        >
                            {notifications.email ? 'Enabled' : 'Disabled'}
                        </Button>
                    </div>
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="font-medium">Telegram Bot</div>
                            <div className="text-sm text-muted-foreground">Get instant alerts via Telegram</div>
                        </div>
                        <Button
                            variant={notifications.telegram ? 'default' : 'outline'}
                            onClick={() => setNotifications({ ...notifications, telegram: !notifications.telegram })}
                        >
                            {notifications.telegram ? 'Enabled' : 'Disabled'}
                        </Button>
                    </div>
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="font-medium">Discord Webhook</div>
                            <div className="text-sm text-muted-foreground">Post predictions to Discord channel</div>
                        </div>
                        <Button
                            variant={notifications.discord ? 'default' : 'outline'}
                            onClick={() => setNotifications({ ...notifications, discord: !notifications.discord })}
                        >
                            {notifications.discord ? 'Enabled' : 'Disabled'}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Prediction Settings */}
            <Card className="bg-card/50">
                <CardHeader>
                    <CardTitle>Prediction Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Minimum Confidence Threshold</Label>
                        <Input type="number" placeholder="50" defaultValue="50" />
                        <p className="text-sm text-muted-foreground">Only show predictions above this confidence level</p>
                    </div>
                    <div className="space-y-2">
                        <Label>Minimum Edge for Value Bets</Label>
                        <Input type="number" placeholder="3" defaultValue="3" />
                        <p className="text-sm text-muted-foreground">Minimum edge percentage to qualify as value bet</p>
                    </div>
                    <Button>Save Settings</Button>
                </CardContent>
            </Card>
        </div>
    )
}
