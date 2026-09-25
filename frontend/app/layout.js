import "./globals.css";

export const metadata = {
  title: "AgentLoom",
  description: "A minimal tool-calling agent orchestrator",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
