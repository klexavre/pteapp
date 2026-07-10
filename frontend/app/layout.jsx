import "./globals.css";

export const metadata = {
  title: "PTE Practice Platform",
  description: "Professional local PTE Repeat Sentence and Word Drill practice",
  icons: {
    icon: "https://mailchimp.com/ctf/images/yzco4xsimv0y/0m8Ef4OX4263uBAFIXHLS/cbd2cb54930c77e844a9bd36a02eb771/favicon-size-graphic_-1.png?w=580&q=70",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
