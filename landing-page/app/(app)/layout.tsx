import { ClientProvider } from "@/components/providers/ClientProvider";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClientProvider>
      <main className="min-h-screen">{children}</main>
    </ClientProvider>
  );
}
