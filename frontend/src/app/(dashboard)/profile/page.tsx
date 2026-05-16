"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import {
    User,
    Mail,
    FileText,
    Camera,
    Save,
    Trash2,
    Loader2,
    ShieldAlert,
    CheckCircle2,
    Sparkles,
    KeyRound,
    Calendar,
} from "lucide-react";

const AVATAR_EMOJIS = [
    { emoji: "🧠", label: "Brain", bg: "from-violet-500 to-indigo-600" },
    { emoji: "🚀", label: "Rocket", bg: "from-blue-400 to-cyan-500" },
    { emoji: "🦁", label: "Lion", bg: "from-amber-400 to-orange-500" },
    { emoji: "🐺", label: "Wolf", bg: "from-slate-500 to-gray-700" },
    { emoji: "🦊", label: "Fox", bg: "from-orange-400 to-red-500" },
    { emoji: "🐉", label: "Dragon", bg: "from-emerald-400 to-teal-600" },
    { emoji: "🦋", label: "Butterfly", bg: "from-pink-400 to-rose-500" },
    { emoji: "🐼", label: "Panda", bg: "from-gray-300 to-slate-500" },
    { emoji: "🦄", label: "Unicorn", bg: "from-purple-400 to-pink-500" },
    { emoji: "🐸", label: "Frog", bg: "from-green-400 to-emerald-600" },
    { emoji: "🤖", label: "Robot", bg: "from-cyan-400 to-blue-600" },
    { emoji: "👻", label: "Ghost", bg: "from-indigo-300 to-violet-500" },
    { emoji: "🎭", label: "Masks", bg: "from-rose-400 to-pink-600" },
    { emoji: "🌙", label: "Moon", bg: "from-slate-600 to-indigo-800" },
    { emoji: "⚡", label: "Lightning", bg: "from-yellow-400 to-amber-500" },
    { emoji: "🔥", label: "Fire", bg: "from-orange-500 to-red-600" },
    { emoji: "🌊", label: "Wave", bg: "from-blue-400 to-indigo-600" },
    { emoji: "🎯", label: "Target", bg: "from-red-400 to-rose-600" },
    { emoji: "💎", label: "Diamond", bg: "from-cyan-300 to-blue-500" },
    { emoji: "🎮", label: "Gaming", bg: "from-violet-400 to-purple-600" },
    { emoji: "🧩", label: "Puzzle", bg: "from-teal-400 to-cyan-600" },
    { emoji: "🌸", label: "Blossom", bg: "from-pink-300 to-rose-400" },
    { emoji: "☀️", label: "Sun", bg: "from-yellow-300 to-orange-400" },
    { emoji: "🎵", label: "Music", bg: "from-purple-400 to-indigo-600" },
];

export default function ProfilePage() {
    const router = useRouter();
    const { user, setUser, logout } = useAuthStore();

    const [fullName, setFullName] = useState(user?.full_name || "");
    const [bio, setBio] = useState(user?.bio || "");
    const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
    const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
    const [selectedEmoji, setSelectedEmoji] = useState<string | null>(null);

    const [saving, setSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [saveError, setSaveError] = useState("");

    const [deleteConfirm, setDeleteConfirm] = useState("");
    const [deleting, setDeleting] = useState(false);
    const [showDeleteZone, setShowDeleteZone] = useState(false);

    const initials = fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2) || "U";

    const joinDate = user?.created_at
        ? new Date(user.created_at).toLocaleDateString("en-US", { month: "long", year: "numeric" })
        : "";

    const handleSave = async () => {
        setSaving(true);
        setSaveError("");
        setSaveSuccess(false);
        try {
            const payload: Record<string, string> = { full_name: fullName, bio };
            if (avatarUrl) payload.avatar_url = avatarUrl;
            if (selectedPreset && selectedEmoji) payload.avatar_url = `emoji:${selectedEmoji}:${selectedPreset}`;
            else if (selectedPreset) payload.avatar_url = `preset:${selectedPreset}`;

            const { data } = await api.patch("/users/me", payload);
            setUser(data);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);
        } catch {
            setSaveError("Failed to save changes. Please try again.");
        } finally {
            setSaving(false);
        }
    };

    const userEmail = user?.email || "";

    const handleDeleteAccount = async () => {
        if (!userEmail || deleteConfirm !== userEmail) return;
        setDeleting(true);
        try {
            await api.delete("/users/me");
            logout();
            router.push("/login");
        } catch {
            setDeleting(false);
            setSaveError("Failed to delete account. Please try again.");
        }
    };

    // Determine avatar display
    const presetGradient = selectedPreset ||
        (user?.avatar_url?.startsWith("preset:") ? user.avatar_url.replace("preset:", "") : null) ||
        (user?.avatar_url?.startsWith("emoji:") ? user.avatar_url.split(":")[2] : null);

    const displayEmoji = selectedEmoji ||
        (user?.avatar_url?.startsWith("emoji:") ? user.avatar_url.split(":")[1] : null);

    return (
        <div className="max-w-3xl mx-auto animate-fade-in pb-16 space-y-8">

            {/* ── Page Header ─────────────────────────────── */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary" />
                        Your Profile
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Customize how you appear across Aethel
                    </p>
                </div>
                {joinDate && (
                    <Badge variant="secondary" className="gap-1.5 text-xs">
                        <Calendar className="w-3 h-3" />
                        Joined {joinDate}
                    </Badge>
                )}
            </div>

            {/* ── Avatar + Name Card ───────────────────────── */}
            <div className="rounded-2xl border border-border/40 bg-card/50 backdrop-blur-sm p-6 space-y-6">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
                    Identity
                </h2>

                {/* Avatar Preview */}
                <div className="flex items-center gap-6">
                    <div className="relative shrink-0">
                        {presetGradient ? (
                            <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${presetGradient} flex items-center justify-center shadow-lg`}>
                                {displayEmoji ? (
                                    <span className="text-3xl">{displayEmoji}</span>
                                ) : (
                                    <span className="text-2xl font-bold text-white">{initials}</span>
                                )}
                            </div>
                        ) : avatarUrl ? (
                            <img
                                src={avatarUrl}
                                alt="Avatar"
                                className="w-20 h-20 rounded-2xl object-cover shadow-lg"
                                onError={() => setAvatarUrl("")}
                            />
                        ) : (
                            <div className="w-20 h-20 rounded-2xl bg-primary/20 flex items-center justify-center shadow-lg border border-primary/30">
                                <span className="text-2xl font-bold text-primary">{initials}</span>
                            </div>
                        )}
                        <div className="absolute -bottom-1.5 -right-1.5 w-6 h-6 rounded-full bg-primary flex items-center justify-center shadow">
                            <Camera className="w-3 h-3 text-primary-foreground" />
                        </div>
                    </div>

                    <div className="flex-1 space-y-1">
                        <p className="text-lg font-semibold">{fullName || "Your Name"}</p>
                        <p className="text-sm text-muted-foreground">{user?.email}</p>
                        <Badge variant="outline" className="text-[10px] capitalize mt-1">
                            {user?.role || "user"}
                        </Badge>
                    </div>
                </div>

                {/* Avatar Emoji Picker */}
                <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                        <Camera className="w-3.5 h-3.5 text-muted-foreground" />
                        Choose your avatar
                    </label>
                    <div className="grid grid-cols-8 gap-2">
                        {AVATAR_EMOJIS.map((preset) => (
                            <button
                                key={preset.emoji}
                                title={preset.label}
                                onClick={() => {
                                    setSelectedEmoji(preset.emoji);
                                    setSelectedPreset(preset.bg);
                                    setAvatarUrl("");
                                }}
                                className={`w-full aspect-square rounded-xl bg-gradient-to-br ${preset.bg} flex items-center justify-center text-2xl transition-all duration-200 hover:scale-110 hover:shadow-lg ${selectedEmoji === preset.emoji
                                        ? "ring-2 ring-offset-2 ring-primary scale-110 shadow-lg"
                                        : ""
                                    }`}
                            >
                                {preset.emoji}
                            </button>
                        ))}
                    </div>
                    <p className="text-xs text-muted-foreground">Pick an emoji avatar — each has its own background color</p>
                </div>

                {/* Custom Avatar URL */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">Or use a custom image URL</label>
                    <div className="relative">
                        <Camera className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="https://example.com/your-photo.jpg"
                            value={avatarUrl}
                            onChange={(e) => {
                                setAvatarUrl(e.target.value);
                                setSelectedPreset(null);
                            }}
                            className="pl-9"
                        />
                    </div>
                </div>

                <Separator className="opacity-30" />

                {/* Full Name */}
                <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                        <User className="w-3.5 h-3.5 text-muted-foreground" />
                        Full Name
                    </label>
                    <Input
                        placeholder="Your full name"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                    />
                </div>

                {/* Email (read-only) */}
                <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                        <Mail className="w-3.5 h-3.5 text-muted-foreground" />
                        Email
                    </label>
                    <Input value={user?.email || ""} disabled className="opacity-60" />
                    <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                </div>

                {/* Bio */}
                <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                        Bio
                    </label>
                    <textarea
                        placeholder="Tell us a little about yourself..."
                        value={bio}
                        onChange={(e) => setBio(e.target.value)}
                        rows={3}
                        maxLength={300}
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
                    />
                    <p className="text-xs text-muted-foreground text-right">{bio.length}/300</p>
                </div>

                {/* Save */}
                {saveError && (
                    <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm border border-destructive/20">
                        {saveError}
                    </div>
                )}

                <Button onClick={handleSave} disabled={saving} className="w-full h-11 font-semibold gap-2">
                    {saving ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
                    ) : saveSuccess ? (
                        <><CheckCircle2 className="w-4 h-4" /> Saved!</>
                    ) : (
                        <><Save className="w-4 h-4" /> Save Changes</>
                    )}
                </Button>
            </div>

            {/* ── Account Info ─────────────────────────────── */}
            <div className="rounded-2xl border border-border/40 bg-card/50 backdrop-blur-sm p-6 space-y-4">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
                    Account
                </h2>
                <div className="space-y-3">
                    {[
                        { icon: KeyRound, label: "Account ID", value: user?.id?.slice(0, 8) + "..." },
                        { icon: ShieldAlert, label: "Role", value: user?.role || "user" },
                        { icon: CheckCircle2, label: "Status", value: user?.is_active ? "Active" : "Inactive" },
                        { icon: Calendar, label: "Member since", value: joinDate },
                    ].map((item) => (
                        <div key={item.label} className="flex items-center justify-between py-2 border-b border-border/10 last:border-0">
                            <span className="text-sm text-muted-foreground flex items-center gap-2">
                                <item.icon className="w-3.5 h-3.5" />
                                {item.label}
                            </span>
                            <Badge variant="secondary" className="text-xs font-mono">
                                {item.value}
                            </Badge>
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Danger Zone ──────────────────────────────── */}
            <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-sm font-semibold text-destructive flex items-center gap-2">
                            <ShieldAlert className="w-4 h-4" />
                            Danger Zone
                        </h2>
                        <p className="text-xs text-muted-foreground mt-0.5">
                            Permanently delete your account and all associated data
                        </p>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        className="border-destructive/40 text-destructive hover:bg-destructive hover:text-destructive-foreground"
                        onClick={() => setShowDeleteZone(!showDeleteZone)}
                    >
                        <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                        Delete Account
                    </Button>
                </div>

                {showDeleteZone && (
                    <div className="space-y-3 pt-2 border-t border-destructive/20 animate-fade-in">
                        <p className="text-sm text-muted-foreground">
                            This will permanently delete your account, all workspaces, documents, and chat history.
                            <strong className="text-foreground"> This cannot be undone.</strong>
                        </p>
                        <div className="space-y-2">
                            <label className="text-sm font-medium block">
                                To confirm, type this email exactly:
                            </label>
                            <div className="px-3 py-2 rounded-md bg-destructive/10 border border-destructive/30 font-mono text-destructive text-sm select-all cursor-text">
                                {userEmail || "loading..."}
                            </div>
                            <Input
                                placeholder="Type your email here"
                                value={deleteConfirm}
                                onChange={(e) => setDeleteConfirm(e.target.value)}
                                className="border-destructive/40 focus-visible:ring-destructive font-mono"
                                disabled={!userEmail}
                            />
                            {deleteConfirm.length > 0 && deleteConfirm !== userEmail && (
                                <p className="text-xs text-destructive">Email doesn't match</p>
                            )}
                            {deleteConfirm === userEmail && userEmail && (
                                <p className="text-xs text-emerald-500">✓ Email confirmed</p>
                            )}
                        </div>
                        <Button
                            variant="destructive"
                            className="w-full"
                            disabled={deleteConfirm !== userEmail || !userEmail || deleting}
                            onClick={handleDeleteAccount}
                        >
                            {deleting ? (
                                <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Deleting everything...</>
                            ) : (
                                <><Trash2 className="w-4 h-4 mr-2" /> Permanently Delete My Account</>
                            )}
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}