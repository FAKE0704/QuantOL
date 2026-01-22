"use client";

import { User, Settings, LogOut } from "lucide-react";
import { useTranslations } from "next-intl";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link } from "@/lib/routing";

interface UserAccountMenuProps {
  username: string;
  onLogout: () => Promise<void>;
}

export function UserAccountMenu({ username, onLogout }: UserAccountMenuProps) {
  const t = useTranslations('account');

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full text-sm font-medium transition-all shadow-md hover:shadow-lg">
          <User className="w-4 h-4" />
          {username}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{username}</p>
            <p className="text-xs leading-none text-slate-400">
              {t('accountLabel')}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/settings" className="cursor-pointer flex items-center">
            <Settings className="h-4 w-4 mr-2" />
            {t('settings')}
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="cursor-pointer text-red-400 focus:text-red-400"
          onClick={onLogout}
        >
          <LogOut className="h-4 w-4 mr-2" />
          {t('logout')}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
