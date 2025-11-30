"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, Sparkles, Plus, Copy, RefreshCw, Database } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import GoogleChart from "./GoogleChart";

const BotGridIcon = ({ animated = false, className = "w-4 h-4" }: { animated?: boolean, className?: string }) => (
  <div 
    className={`grid grid-cols-2 gap-0.5 ${className} ${animated ? 'animate-spin' : ''}`} 
    style={animated ? { animationDirection: 'reverse', animationDuration: '1s' } : {}}
  >
    <div className={`bg-current rounded-[1px] w-full h-full ${animated ? 'opacity-100' : 'opacity-90'}`}></div>
    <div className={`bg-current rounded-[1px] w-full h-full ${animated ? 'opacity-40' : 'opacity-90'}`}></div>
    <div className={`bg-current rounded-[1px] w-full h-full ${animated ? 'opacity-40' : 'opacity-90'}`}></div>
    <div className={`bg-current rounded-[1px] w-full h-full ${animated ? 'opacity-40' : 'opacity-90'}`}></div>
  </div>
);

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isTyping?: boolean;
  displayedContent?: string;
  visualization?: any;
  sql_query?: string;
  showSql?: boolean;
}

interface ChatBoxProps {
  locationId: string;
  productId: string;
}

export default function ChatBox({ locationId, productId }: ChatBoxProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);

  const handleNewChat = () => {
    setMessages([]);
    setInput("");
    setLoading(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Check if user is near bottom
  const isNearBottom = () => {
    if (!chatContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    return scrollHeight - scrollTop - clientHeight < 100; // Within 100px of bottom
  };

  // Auto-scroll only if user is near bottom
  useEffect(() => {
    if (!isUserScrolling && isNearBottom()) {
      scrollToBottom();
    }
  }, [messages, isUserScrolling]);

  // Typewriter effect
  useEffect(() => {
    const typingMessage = messages.find(m => m.isTyping && m.role === "assistant");
    if (!typingMessage) return;

    const fullContent = typingMessage.content;
    const currentLength = typingMessage.displayedContent?.length || 0;

    if (currentLength < fullContent.length) {
      const timer = setTimeout(() => {
        setMessages(prev => prev.map(msg => {
          if (msg === typingMessage) {
            return {
              ...msg,
              displayedContent: fullContent.slice(0, currentLength + 15)
            };
          }
          return msg;
        }));
      }, 5);

      return () => clearTimeout(timer);
    } else {
      setMessages(prev => prev.map(msg => {
        if (msg === typingMessage) {
          return { ...msg, isTyping: false, displayedContent: fullContent };
        }
        return msg;
      }));
    }
  }, [messages]);

  const requestAssistantResponse = async (textToSend: string, options?: { replaceIndex?: number }) => {
    try {
      const response = await fetch("http://localhost:8000/api/v1/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: textToSend,
          location_id: locationId,
          product_id: productId,
          use_rag: true,
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer || "Sorry, I couldn't process your request.",
        timestamp: new Date(),
        isTyping: true,
        displayedContent: "",
        visualization: data.visualization,
        sql_query: data.sql_query
      };

      if (typeof options?.replaceIndex === "number") {
        setMessages((prev) => prev.map((msg, idx) => idx === options.replaceIndex ? assistantMessage : msg));
      } else {
        setMessages((prev) => [...prev, assistantMessage]);
      }
      setIsUserScrolling(false);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, there was an error processing your request.",
        timestamp: new Date(),
        isTyping: false,
      };
      if (typeof options?.replaceIndex === "number") {
        setMessages((prev) => prev.map((msg, idx) => idx === options.replaceIndex ? errorMessage : msg));
      } else {
        setMessages((prev) => [...prev, errorMessage]);
      }
      setIsUserScrolling(false);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: textToSend,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setIsUserScrolling(false); // Force scroll to show user's message
    
    // Immediate scroll to show user message
    setTimeout(() => scrollToBottom(), 100);
    requestAssistantResponse(textToSend);
  };

  const toggleSql = (index: number) => {
    setMessages(prev => prev.map((msg, i) => 
      i === index ? { ...msg, showSql: !msg.showSql } : msg
    ));
  };

  const markdownToPlainText = (markdown: string) => {
    if (!markdown) return "";
    return markdown
      .replace(/```[\s\S]*?```/g, (block) => block.replace(/```[a-zA-Z]*\n?/g, "").replace(/```/g, ""))
      .replace(/`([^`]+)`/g, "$1")
      .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
      .replace(/^>\s?/gm, "")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/^[-*+]\s+/gm, "")
      .replace(/^\d+\.\s+/gm, "")
      .replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, "$1")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const regenerateResponse = (index: number) => {
    const previousUserMessage = [...messages.slice(0, index)].reverse().find((msg) => msg.role === "user");
    if (!previousUserMessage) return;
    setLoading(true);
    setIsUserScrolling(false);
    requestAssistantResponse(previousUserMessage.content, { replaceIndex: index });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Chat Header */}
      <div className="px-4 py-2.5 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#D04A02] to-[#A83C02] rounded-full flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Plan IQ</h2>
            </div>
          </div>
          
          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-[#D04A02] hover:text-[#D04A02] transition-all duration-200 shadow-sm"
            title="Start New Chat"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-6 py-6"
        onScroll={(e) => {
          const target = e.currentTarget;
          const isAtBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 50;
          setIsUserScrolling(!isAtBottom);
        }}
      >
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-3xl">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-orn-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                How can I help you today?
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                Ask me about inventory, forecasts, events, weather impact, or any supply chain insights.
              </p>
              
              {/* Suggested Questions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-left">
                {[
                  "Which products in the Northeast are expected to see the biggest weather-driven uptick in demand over the next month?",
                  "Which store locations will see the largest weather-related rise or drop in demand next week?",
                  "Which product categories have the biggest change in weather-demand (positive and negative)?",
                  "Sandwich sales were down in the Southeast last month. How much of that was due to the weather and how was demand for related products such as tomatoes, lettuce also impacted?",
                  "Which cities are hosting pro football games this week, and what are the highest weather-impacted food categories in these markets?",
                  "A music festival is expected to drive increased foot traffic in Nashville — what products should I stock up on?"
                ].map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(question)}
                    className="text-xs text-left p-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 hover:border-[#D04A02] rounded-lg transition-all duration-200 text-gray-700 hover:text-[#D04A02]"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="space-y-6 max-w-4xl mx-auto">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 bg-gradient-to-br from-[#D04A02] to-[#A83C02] rounded-full flex items-center justify-center flex-shrink-0">
                  <BotGridIcon className="w-4 h-4 text-white" />
                </div>
              )}

              <div className={`flex-1 max-w-3xl ${msg.role === "user" ? "flex justify-end" : ""}`}>
                <div
                  className={`${
                    msg.role === "user"
                      ? "bg-[#D04A02] text-white rounded-2xl rounded-tr-sm px-4 py-3 inline-block"
                      : "text-gray-900"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ node, inline, className, children, ...props }: any) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={vscDarkPlus}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code className={className} style={{
                                backgroundColor: '#f3f4f6',
                                padding: '0.2rem 0.4rem',
                                borderRadius: '0.25rem',
                                fontSize: '0.875em',
                                fontFamily: 'monospace'
                              }} {...props}>
                                {children}
                              </code>
                            );
                          },
                          // Enhanced table styling
                          table: ({ children }) => (
                            <div style={{ 
                              overflowX: 'auto', 
                              marginTop: '1rem', 
                              marginBottom: '1.5rem',
                              borderRadius: '0.5rem',
                              border: '1px solid #E5E7EB',
                              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                            }}>
                              <table style={{
                                width: '100%',
                                borderCollapse: 'collapse',
                                fontSize: '0.875rem'
                              }}>
                                {children}
                              </table>
                            </div>
                          ),
                          thead: ({ children }) => (
                            <thead style={{
                              backgroundColor: '#F9FAFB',
                              borderBottom: '2px solid #E5E7EB'
                            }}>
                              {children}
                            </thead>
                          ),
                          tbody: ({ children }) => (
                            <tbody style={{ backgroundColor: '#FFFFFF' }}>
                              {children}
                            </tbody>
                          ),
                          tr: ({ children, ...props }: any) => (
                            <tr style={{
                              borderBottom: '1px solid #E5E7EB',
                              transition: 'background-color 0.15s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F9FAFB'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                            {...props}>
                              {children}
                            </tr>
                          ),
                          th: ({ children }) => (
                            <th style={{
                              padding: '0.75rem 1rem',
                              textAlign: 'left',
                              fontWeight: '600',
                              color: '#374151',
                              fontSize: '0.875rem',
                              letterSpacing: '0.025em'
                            }}>
                              {children}
                            </th>
                          ),
                          td: ({ children }) => (
                            <td style={{
                              padding: '0.75rem 1rem',
                              color: '#1F2937'
                            }}>
                              {children}
                            </td>
                          ),
                          // Enhanced headings
                          h1: ({ children }) => (
                            <h1 style={{
                              fontSize: '1.5rem',
                              fontWeight: '700',
                              marginTop: '1.5rem',
                              marginBottom: '1rem',
                              color: '#111827',
                              borderBottom: '2px solid #D04A02',
                              paddingBottom: '0.5rem'
                            }}>{children}</h1>
                          ),
                          h2: ({ children }) => (
                            <h2 style={{
                              fontSize: '1.25rem',
                              fontWeight: '600',
                              marginTop: '1.25rem',
                              marginBottom: '0.75rem',
                              color: '#1F2937'
                            }}>{children}</h2>
                          ),
                          h3: ({ children }) => (
                            <h3 style={{
                              fontSize: '1.1rem',
                              fontWeight: '600',
                              marginTop: '1rem',
                              marginBottom: '0.5rem',
                              color: '#374151'
                            }}>{children}</h3>
                          ),
                          p: ({ children }) => <p className="mb-3 leading-relaxed text-gray-800">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc ml-6 mb-3 space-y-2">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal ml-6 mb-3 space-y-2">{children}</ol>,
                          li: ({ children }) => <li className="leading-relaxed text-gray-700">{children}</li>,
                          strong: ({ children }) => <strong style={{ fontWeight: '600', color: '#111827' }}>{children}</strong>,
                          em: ({ children }) => <em style={{ fontStyle: 'italic', color: '#4B5563' }}>{children}</em>,
                          blockquote: ({ children }) => (
                            <blockquote style={{
                              borderLeft: '4px solid #D04A02',
                              paddingLeft: '1rem',
                              marginLeft: '0',
                              marginTop: '1rem',
                              marginBottom: '1rem',
                              fontStyle: 'italic',
                              color: '#4B5563'
                            }}>
                              {children}
                            </blockquote>
                          ),
                        }}
                      >
                        {msg.displayedContent || msg.content}
                      </ReactMarkdown>

                      {/* Chart Visualization - Clean Centered Display */}
                      {msg.visualization?.chart_config && msg.visualization.ready && (
                        <div style={{ 
                          marginTop: '1rem',
                          marginBottom: '-1.5rem',
                          marginLeft: '-1.5rem',
                          marginRight: '-1.5rem',
                          width: 'calc(100% + 3rem)',
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                          padding: 0,
                          borderRadius: '0 0 1rem 1rem'
                        }}>
                          <GoogleChart chartConfig={msg.visualization.chart_config} />
                        </div>
                      )}

                      {/* Action Icons */}
                      {!msg.isTyping && (
                        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-100">
                          <button 
                            onClick={() => copyToClipboard(markdownToPlainText(msg.content))}
                            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                            title="Copy Answer"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>
                          
                          <button 
                            onClick={() => regenerateResponse(idx)}
                            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                            title="Regenerate Answer"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                          </button>

                          {msg.sql_query && (
                            <button 
                              onClick={() => toggleSql(idx)}
                              className={`p-1 rounded transition-colors flex items-center gap-1 ${
                                msg.showSql 
                                  ? "text-[#D04A02] bg-orange-50" 
                                  : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                              }`}
                              title="Show SQL Query"
                            >
                              <Database className="w-3.5 h-3.5" />
                              {msg.showSql && <span className="text-xs font-medium">SQL</span>}
                            </button>
                          )}
                        </div>
                      )}

                      {/* SQL Query Dropdown */}
                      {msg.showSql && msg.sql_query && (
                        <div className="mt-3 rounded-lg overflow-hidden border border-gray-800 bg-[#0b1120]/95">
                          <div className="flex items-center justify-between px-3 py-1.5 bg-[#111827] border-b border-gray-800">
                            <span className="text-xs font-medium text-gray-300">Generated SQL</span>
                            <button 
                              onClick={() => copyToClipboard(msg.sql_query!)}
                              className="text-gray-400 hover:text-white transition-colors"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                          <div className="px-3 py-2 overflow-x-auto text-gray-100 font-mono text-xs leading-relaxed">
                            <pre className="whitespace-pre-wrap">{msg.sql_query}</pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm">{msg.content}</p>
                  )}
                </div>
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 bg-gradient-to-br from-[#D04A02] to-[#A83C02] rounded-full flex items-center justify-center">
                <BotGridIcon className="w-4 h-4 text-white" animated />
              </div>
              <div className="flex items-center">
                <span className="text-gray-500 text-sm font-medium animate-pulse">Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-3 bg-gray-50 rounded-2xl p-2 border border-gray-200 focus-within:border-[#D04A02] transition-colors">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Plan IQ..."
              className="flex-1 bg-transparent resize-none outline-none px-3 py-2 text-sm text-gray-900 placeholder-gray-400 max-h-32"
              rows={1}
              disabled={loading}
              style={{
                minHeight: '20px',
                height: 'auto',
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = target.scrollHeight + 'px';
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all ${
                loading || !input.trim()
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                  : "bg-[#D04A02] text-white hover:bg-[#A83C02] shadow-sm"
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
