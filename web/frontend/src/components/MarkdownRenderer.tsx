"use client";

import Markdown from "markdown-to-jsx";

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  if (!content) {
    return <p className="text-sm text-gray-500">No content available.</p>;
  }

  return (
    <div className="prose prose-sm max-w-none text-gray-700">
      <Markdown
        options={{
          overrides: {
            h1: { props: { className: "text-2xl font-bold mt-6 mb-3 text-gray-900" } },
            h2: { props: { className: "text-xl font-semibold mt-5 mb-2 text-gray-900" } },
            h3: { props: { className: "text-lg font-semibold mt-4 mb-2 text-gray-800" } },
            h4: { props: { className: "text-base font-semibold mt-3 mb-1 text-gray-800" } },
            p: { props: { className: "mb-3 leading-relaxed" } },
            ul: { props: { className: "list-disc pl-5 mb-3 space-y-1" } },
            ol: { props: { className: "list-decimal pl-5 mb-3 space-y-1" } },
            li: { props: { className: "leading-relaxed" } },
            strong: { props: { className: "font-semibold text-gray-900" } },
            blockquote: {
              props: {
                className:
                  "border-l-4 border-gray-300 pl-4 italic text-gray-600 my-3",
              },
            },
            code: { props: { className: "bg-gray-100 rounded px-1.5 py-0.5 text-sm font-mono text-gray-800" } },
            pre: { props: { className: "bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto my-3 text-sm" } },
            a: { props: { className: "text-blue-600 underline hover:text-blue-800" } },
            table: { props: { className: "min-w-full border-collapse border border-gray-200 my-3" } },
            th: { props: { className: "border border-gray-200 bg-gray-50 px-3 py-2 text-left text-sm font-semibold" } },
            td: { props: { className: "border border-gray-200 px-3 py-2 text-sm" } },
            hr: { props: { className: "my-6 border-gray-200" } },
          },
        }}
      >
        {content}
      </Markdown>
    </div>
  );
}
