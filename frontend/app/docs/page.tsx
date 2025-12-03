"use client";

import React, { useState } from "react";
import { 
  Book, 
  Code, 
  Database, 
  Server, 
  Layers, 
  FileText, 
  Cpu, 
  Globe, 
  Shield,
  Terminal,
  ChevronRight,
  Menu,
  X,
  Package,
  GitBranch,
  Zap,
  Lock,
  Activity,
  Settings,
  Cloud,
  CheckCircle,
  AlertCircle,
  Search
} from "lucide-react";
import Link from "next/link";

export default function DocumentationPage() {
  const [activeSection, setActiveSection] = useState("overview");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const sections = [
    { id: "overview", label: "Overview", icon: Book },
    { id: "architecture", label: "Architecture", icon: Layers },
    { id: "tech-stack", label: "Tech Stack", icon: Code },
    { id: "api-reference", label: "API Reference", icon: Server },
    { id: "database", label: "Database Schema", icon: Database },
    { id: "agents", label: "AI Agents", icon: Cpu },
    { id: "frontend", label: "Frontend Structure", icon: Globe },
    { id: "backend", label: "Backend Structure", icon: Server },
    { id: "deployment", label: "Deployment", icon: Terminal },
    { id: "security", label: "Security", icon: Shield },
    { id: "setup", label: "Setup Guide", icon: Settings },
  ];

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Track scroll position to update active section
  React.useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 100;
      
      for (const section of sections) {
        const element = document.getElementById(section.id);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="flex h-screen bg-white text-gray-900 font-sans">
      {/* Sidebar Navigation */}
      <aside 
        className={`${
          isSidebarOpen ? "w-64" : "w-0"
        } bg-gray-50 border-r border-gray-200 transition-all duration-300 overflow-hidden flex flex-col fixed md:relative z-20 h-full`}
      >
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-white">
          <div className="flex items-center gap-2 font-bold text-xl text-[#D04A02]">
            <Book className="w-6 h-6" />
            <span>Plan IQ Docs</span>
          </div>
          <button onClick={() => setIsSidebarOpen(false)} className="md:hidden">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => scrollToSection(section.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                activeSection === section.id
                  ? "bg-[#D04A02] text-white shadow-lg scale-105 font-semibold"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900 hover:scale-102"
              }`}
            >
              <section.icon className={`w-4 h-4 transition-transform duration-200 ${
                activeSection === section.id ? "scale-110" : ""
              }`} />
              {section.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <Link href="/" className="flex items-center gap-2 text-sm text-gray-600 hover:text-[#D04A02] transition-colors">
            <ChevronRight className="w-4 h-4" />
            Back to App
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto h-full relative">
        {/* Mobile Header */}
        <div className="md:hidden sticky top-0 bg-white border-b border-gray-200 p-4 z-10 flex items-center gap-3">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            <Menu className="w-6 h-6 text-gray-600" />
          </button>
          <span className="font-bold text-lg">Documentation</span>
        </div>

        <div className="max-w-4xl mx-auto p-8 space-y-12">
          
          {/* Overview */}
          <section id="overview" className="scroll-mt-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-6">Plan IQ Documentation</h1>
            <div className="bg-gradient-to-r from-orange-50 to-red-50 border-l-4 border-[#D04A02] p-6 rounded-r-lg mb-8">
              <p className="text-xl text-gray-700 leading-relaxed">
                <strong>Plan IQ</strong> is an enterprise-grade, AI-powered supply chain intelligence platform. 
                It leverages a <strong>Hybrid Agentic RAG</strong> architecture powered by <strong>Azure OpenAI (GPT-4)</strong>, 
                <strong>Azure AI Search</strong>, and <strong>Gremlin Knowledge Graph</strong> to provide 
                real-time analytics, demand forecasting, and actionable insights.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="p-6 bg-orange-50 rounded-xl border border-orange-200 hover:shadow-lg transition-shadow">
                <Cpu className="w-10 h-10 text-[#D04A02] mb-4" />
                <h3 className="font-bold text-lg mb-2">Multi-Agent AI System</h3>
                <p className="text-sm text-gray-600 mb-3">Orchestrated by LangGraph and exposed via <strong>Model Context Protocol (MCP)</strong>.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />MCP Server Integration</li>
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />LangGraph Orchestration</li>
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />5 Specialized Agents</li>
                </ul>
              </div>
              
              <div className="p-6 bg-blue-50 rounded-xl border border-blue-200 hover:shadow-lg transition-shadow">
                <Database className="w-10 h-10 text-blue-600 mb-4" />
                <h3 className="font-bold text-lg mb-2">Hybrid Data Layer</h3>
                <p className="text-sm text-gray-600 mb-3">Combines SQL, Vector Search, and Graph data for complete context.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-blue-600" />PostgreSQL (Transactional)</li>
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-blue-600" />Azure AI Search (Vector)</li>
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-blue-600" />Gremlin Graph (Relationships)</li>
                </ul>
              </div>
              
              <div className="p-6 bg-green-50 rounded-xl border border-green-200 hover:shadow-lg transition-shadow">
                <Zap className="w-10 h-10 text-green-600 mb-4" />
                <h3 className="font-bold text-lg mb-2">Intelligent RAG</h3>
                <p className="text-sm text-gray-600 mb-3">Context-aware SQL generation using Entity Resolution and Graph Expansion.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />Entity Resolution</li>
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />Context Expansion</li>
                  <li className="flex items-start gap-2"><CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />Schema-aware SQL</li>
                </ul>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-xl font-bold mb-4">Key Features</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <Activity className="w-5 h-5 text-[#D04A02] mt-1" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Real-time Analytics Dashboard</h4>
                    <p className="text-sm text-gray-600">Interactive visualizations with role-based views for Store Managers, CFOs, Planners, and Marketing teams.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Cpu className="w-5 h-5 text-[#D04A02] mt-1" />
                  <div>
                    <h4 className="font-semibold text-gray-900">AI-Powered Chat Interface</h4>
                    <p className="text-sm text-gray-600">Natural language queries converted to SQL, with dynamic chart generation and insights.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Cloud className="w-5 h-5 text-[#D04A02] mt-1" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Weather Impact Analysis</h4>
                    <p className="text-sm text-gray-600">Azure Maps integration for real-time weather tracking and demand forecasting.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-[#D04A02] mt-1" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Enterprise Security</h4>
                    <p className="text-sm text-gray-600">JWT authentication, bcrypt password hashing, and CORS protection.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Architecture */}
          <section id="architecture" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Layers className="w-8 h-8 text-[#D04A02]" />
              System Architecture
            </h2>
            
            <p className="text-gray-700 mb-6 leading-relaxed">
              Plan IQ follows a modern <strong>Hybrid Agentic RAG</strong> architecture. It combines a traditional web stack 
              with an advanced AI layer that uses <strong>Model Context Protocol (MCP)</strong> to expose agents to external tools.
              The data layer is a hybrid of <strong>PostgreSQL</strong> (Structured), <strong>Azure AI Search</strong> (Unstructured/Vector), 
              and <strong>Gremlin Graph Database</strong> (Relationships).
            </p>

            <div className="bg-gray-900 text-gray-300 p-6 rounded-xl font-mono text-sm overflow-x-auto mb-8 shadow-lg">
              <pre className="whitespace-pre">{`
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                                  │
│                        Next.js 14 Frontend (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Dashboard   │  │   ChatBox    │  │  Charts &    │  │ Weather Map  │   │
│  │  Components  │  │  Interface   │  │ Visualizations│  │ (Azure Maps) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LOGIC LAYER                                │
│                  FastAPI Backend + MCP Server (Python)                       │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    ORCHESTRATOR AGENT (LangGraph)                  │     │
│  │  • Intent Classification  • Agent Selection  • Response Synthesis  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    ↕                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   Database   │ │Visualization │ │   Weather    │ │   Events     │      │
│  │    Agent     │ │    Agent     │ │    Agent     │ │    Agent     │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│          ↕                 ↕                 ↕                 ↕            │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │  MCP Server  │◄──│     Azure    │   │  Inventory   │   │  Location    │  │
│  │  Interface   │   │ (OpenAI API) │   │    Agent     │   │    Agent     │  │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↕ Queries
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER (Hybrid)                               │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐ │
│  │      PostgreSQL      │  │    Azure AI Search   │  │    Gremlin Graph   │ │
│  │    (Transactional)   │  │   (Vector/Semantic)  │  │   (Relationships)  │ │
│  ├──────────────────────┤  ├──────────────────────┤  ├────────────────────┤ │
│  │ • Sales & Revenue    │  │ • Entity Resolution  │  │ • Product Hierarchy│ │
│  │ • Inventory Levels   │  │ • Product Catalog    │  │ • Supply Chain Map │ │
│  │ • Weather History    │  │ • Location Index     │  │ • Event Impact     │ │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↕
                        ┌─────────────────────────┐
                        │    Azure OpenAI GPT-4   │
                        │  • Text Generation      │
                        │  • SQL Generation       │
                        │  • Embeddings           │
                        └─────────────────────────┘
              `}</pre>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <h3 className="font-bold text-lg mb-3 text-gray-900">Data Flow: User Query</h3>
                <ol className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="bg-[#D04A02] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">1</span>
                    <span>User enters natural language query in ChatBox</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="bg-[#D04A02] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">2</span>
                    <span>Orchestrator Agent analyzes intent using GPT-4</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="bg-[#D04A02] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">3</span>
                    <span><strong>Azure AI Search</strong> resolves entities (e.g., "Coke" → "P-101")</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="bg-[#D04A02] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">4</span>
                    <span><strong>Gremlin Graph</strong> expands context (e.g., find related products)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="bg-[#D04A02] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">5</span>
                    <span>Database Agent generates context-aware SQL query</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="bg-[#D04A02] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">6</span>
                    <span>Query executed on PostgreSQL, results returned</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="bg-[#D04A02] text-white rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">7</span>
                    <span>Visualization Agent creates chart configuration</span>
                  </li>
                </ol>
              </div>
              
              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <h3 className="font-bold text-lg mb-3 text-gray-900">Agent Orchestration (LangGraph)</h3>
                <div className="space-y-3 text-sm text-gray-700">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">State Machine Workflow:</h4>
                    <div className="bg-gray-50 p-3 rounded border border-gray-200 font-mono text-xs">
                      classify_intent → resolve_entities → expand_context → execute_agents → synthesize_response
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Context Resolution:</h4>
                    <ul className="space-y-1 text-xs">
                      <li>• <strong>Entity Resolution:</strong> Azure AI Search finds exact IDs from vague terms</li>
                      <li>• <strong>Graph Expansion:</strong> Gremlin finds relationships (Category, Region)</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">Response Synthesis:</h4>
                    <p className="text-xs">Combines outputs from multiple agents into coherent natural language response with optional visualizations.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Tech Stack */}
          <section id="tech-stack" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Code className="w-8 h-8 text-[#D04A02]" />
              Technology Stack
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Frontend Stack */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 pb-2 border-b border-gray-200 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-600" />
                  Frontend Technologies
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Core Framework</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#D04A02] rounded-full"></div>
                        <strong>Next.js 14</strong> - React framework with App Router
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#D04A02] rounded-full"></div>
                        <strong>TypeScript</strong> - Type-safe development
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#D04A02] rounded-full"></div>
                        <strong>React 18</strong> - UI library with hooks
                      </li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Styling & UI</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <strong>Tailwind CSS 3</strong> - Utility-first CSS (PwC Theme)
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <strong>Lucide React</strong> - Icon library
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <strong>Class Variance Authority</strong> - Component variants
                      </li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Data Visualization</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <strong>Google Charts</strong> - Interactive charts
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <strong>Azure Maps Control</strong> - Weather maps
                      </li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Content & State</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <strong>React Markdown</strong> - Markdown rendering
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <strong>Zustand</strong> - State management
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <strong>Axios</strong> - HTTP client
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
              
              {/* Backend Stack */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 pb-2 border-b border-gray-200 flex items-center gap-2">
                  <Server className="w-5 h-5 text-green-600" />
                  Backend Technologies
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Core Framework</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#D04A02] rounded-full"></div>
                        <strong>Python 3.11+</strong> - Programming language
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#D04A02] rounded-full"></div>
                        <strong>FastAPI</strong> - Modern async web framework
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#D04A02] rounded-full"></div>
                        <strong>Uvicorn</strong> - ASGI server
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#D04A02] rounded-full"></div>
                        <strong>Pydantic</strong> - Data validation
                      </li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">AI & Machine Learning</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <strong>LangChain</strong> - LLM framework
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <strong>LangGraph</strong> - Agent orchestration
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <strong>MCP</strong> - Model Context Protocol
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <strong>Azure OpenAI</strong> - GPT-4 & Embeddings
                      </li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Database & ORM</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <strong>SQLAlchemy 2.0</strong> - ORM for PostgreSQL
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <strong>psycopg2</strong> - PostgreSQL adapter
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <strong>Alembic</strong> - Database migrations
                      </li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Security & Utilities</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <strong>python-jose</strong> - JWT tokens
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <strong>passlib</strong> - Password hashing (bcrypt)
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <strong>python-dotenv</strong> - Environment variables
                      </li>
                      <li className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <strong>tenacity</strong> - Retry logic
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4 text-gray-900">Cloud & Infrastructure</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Azure Services</h4>
                  <ul className="space-y-1 text-gray-700">
                    <li>• Azure OpenAI (GPT-4)</li>
                    <li>• Azure AI Search (Vector)</li>
                    <li>• Azure Maps</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Database</h4>
                  <ul className="space-y-1 text-gray-700">
                    <li>• PostgreSQL 14+</li>
                    <li>• Gremlin API (Cosmos DB)</li>
                    <li>• Redis (Caching)</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Monitoring</h4>
                  <ul className="space-y-1 text-gray-700">
                    <li>• Prometheus Client</li>
                    <li>• JSON Logger</li>
                    <li>• Structured Logging</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* API Reference */}
          <section id="api-reference" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Server className="w-8 h-8 text-[#D04A02]" />
              API Reference
            </h2>
            
            <p className="text-gray-700 mb-6">
              The backend exposes RESTful API endpoints organized into three main categories: 
              <strong> Chat/AI</strong>, <strong>Analytics</strong>, and <strong>Reports</strong>. 
              All endpoints return JSON responses and support CORS for frontend integration.
            </p>

            <div className="space-y-6">
              {/* Chat Endpoints */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Chat & AI Endpoints</h3>
                
                <div className="border border-gray-200 rounded-lg overflow-hidden mb-4">
                  <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-3">
                    <span className="bg-green-100 text-green-700 px-3 py-1 rounded text-xs font-bold">POST</span>
                    <code className="text-sm font-mono text-gray-900">/api/v1/chat</code>
                    <span className="ml-auto text-xs text-gray-500">Primary Chat Endpoint</span>
                  </div>
                  <div className="p-5 bg-white">
                    <p className="text-gray-700 mb-4">
                      Main endpoint for AI chatbot. Processes natural language queries using the multi-agent system 
                      and returns responses with optional visualizations.
                    </p>
                    
                    <h4 className="text-sm font-bold text-gray-900 mb-2">Request Body:</h4>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded text-xs overflow-x-auto mb-4">
{`{
  "query": "Show me sales trends for New York",
  "product_id": "P123",           // Optional
  "location_id": "L456",          // Optional
  "session_id": "uuid-string"     // Optional
}`}
                    </pre>
                    
                    <h4 className="text-sm font-bold text-gray-900 mb-2">Response:</h4>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded text-xs overflow-x-auto mb-4">
{`{
  "query": "Show me sales trends...",
  "answer": "Here are the sales trends...",
  "sql_query": "SELECT date, SUM(amount)...",
  "data_source": "postgresql",
  "row_count": 30,
  "raw_data": [...],
  "visualization": {
    "type": "LineChart",
    "data": [...],
    "options": {...}
  },
  "intent": "data_query",
  "status": "success"
}`}
                    </pre>

                    <h4 className="text-sm font-bold text-gray-900 mb-2">Features:</h4>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                        Automatic SQL generation from natural language
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                        Dynamic chart configuration based on data
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                        Multi-agent orchestration via LangGraph
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-3">
                    <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-xs font-bold">GET</span>
                    <code className="text-sm font-mono text-gray-900">/api/v1/chat/stats</code>
                  </div>
                  <div className="p-5 bg-white">
                    <p className="text-gray-700">Get orchestrator statistics and performance metrics.</p>
                  </div>
                </div>
              </div>

              {/* Analytics Endpoints */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Analytics Endpoints</h3>
                
                <div className="space-y-4">
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-3">
                      <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-xs font-bold">GET</span>
                      <code className="text-sm font-mono text-gray-900">/api/v1/analytics/kpis</code>
                    </div>
                    <div className="p-5 bg-white">
                      <p className="text-gray-700 mb-3">Retrieves Key Performance Indicators for the dashboard.</p>
                      
                      <h4 className="text-sm font-bold text-gray-900 mb-2">Query Parameters:</h4>
                      <ul className="text-sm text-gray-700 space-y-1 mb-3">
                        <li><code className="bg-gray-100 px-2 py-0.5 rounded">days</code> (int, default: 30) - Analysis period</li>
                        <li><code className="bg-gray-100 px-2 py-0.5 rounded">location_id</code> (string, optional) - Filter by location</li>
                      </ul>
                      
                      <h4 className="text-sm font-bold text-gray-900 mb-2">Response:</h4>
                      <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-x-auto">
{`{
  "total_sales": 125000,
  "total_revenue": 2500000.50,
  "avg_stock_level": 450,
  "low_stock_items": 12,
  "period": "Last 30 days"
}`}
                      </pre>
                    </div>
                  </div>

                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-3">
                      <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-xs font-bold">GET</span>
                      <code className="text-sm font-mono text-gray-900">/api/v1/analytics/trends/sales</code>
                    </div>
                    <div className="p-5 bg-white">
                      <p className="text-gray-700 mb-3">Fetches historical sales data for time-series charts.</p>
                      
                      <h4 className="text-sm font-bold text-gray-900 mb-2">Query Parameters:</h4>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li><code className="bg-gray-100 px-2 py-0.5 rounded">product_id</code> - Filter by product</li>
                        <li><code className="bg-gray-100 px-2 py-0.5 rounded">location_id</code> - Filter by location</li>
                        <li><code className="bg-gray-100 px-2 py-0.5 rounded">days</code> - Number of days (1-365)</li>
                      </ul>
                    </div>
                  </div>

                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-3">
                      <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-xs font-bold">GET</span>
                      <code className="text-sm font-mono text-gray-900">/api/v1/analytics/weather-impact</code>
                    </div>
                    <div className="p-5 bg-white">
                      <p className="text-gray-700">Analyze weather impact on sales for a specific location.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Reports Endpoints */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Reports & Data Management</h3>
                
                <div className="space-y-4">
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-3">
                      <span className="bg-green-100 text-green-700 px-3 py-1 rounded text-xs font-bold">POST</span>
                      <code className="text-sm font-mono text-gray-900">/api/v1/reports/ingest</code>
                    </div>
                    <div className="p-5 bg-white">
                      <p className="text-gray-700 mb-3">Ingest data into PostgreSQL database (sales, inventory, weather, events).</p>
                      
                      <h4 className="text-sm font-bold text-gray-900 mb-2">Request Body:</h4>
                      <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-x-auto">
{`{
  "data_type": "sales",  // or "inventory", "weather", "events"
  "records": [
    {
      "product_id": "P123",
      "location_id": "L456",
      "date": "2024-01-15",
      "amount": 1500.00
      // ... other fields
    }
  ]
}`}
                      </pre>
                    </div>
                  </div>

                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-3">
                      <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-xs font-bold">GET</span>
                      <code className="text-sm font-mono text-gray-900">/api/v1/reports/database-stats</code>
                    </div>
                    <div className="p-5 bg-white">
                      <p className="text-gray-700">Get database statistics including record counts for all tables.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* API Documentation Links */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
                <h3 className="font-bold text-lg mb-3 text-gray-900">Interactive API Documentation</h3>
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-2">Swagger UI</h4>
                    <p className="text-sm text-gray-600 mb-2">Interactive API explorer with request/response examples</p>
                    <code className="text-xs bg-white px-2 py-1 rounded border border-blue-200">http://localhost:8000/api/docs</code>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-2">ReDoc</h4>
                    <p className="text-sm text-gray-600 mb-2">Clean, searchable API documentation</p>
                    <code className="text-xs bg-white px-2 py-1 rounded border border-blue-200">http://localhost:8000/api/redoc</code>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Database Schema */}
          <section id="database" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Database className="w-8 h-8 text-[#D04A02]" />
              Data Layer Schema
            </h2>
            
            <p className="text-gray-700 mb-6">
              Plan IQ uses a <strong>Hybrid Data Architecture</strong>:
              <ul className="list-disc ml-6 mt-2 space-y-1">
                <li><strong>PostgreSQL</strong>: Transactional data (Sales, Inventory)</li>
                <li><strong>Azure AI Search</strong>: Vector indexes for entity resolution</li>
                <li><strong>Gremlin Graph</strong>: Knowledge graph for relationships</li>
              </ul>
            </p>

            {/* PostgreSQL Tables */}
            <div className="mb-8">
              <h3 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-600" />
                PostgreSQL Tables
              </h3>
              
              <div className="overflow-x-auto bg-white border border-gray-200 rounded-lg">
                <table className="min-w-full text-sm text-left text-gray-600">
                  <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 border-b font-semibold">Table Name</th>
                      <th className="px-6 py-3 border-b font-semibold">Description</th>
                      <th className="px-6 py-3 border-b font-semibold">Key Columns</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="bg-white border-b hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">Metrics (SalesData)</td>
                      <td className="px-6 py-4">Transactional sales and revenue records</td>
                      <td className="px-6 py-4 font-mono text-xs">product_id, location_id, week_end_date, sales_units, revenue</td>
                    </tr>
                    <tr className="bg-gray-50 border-b hover:bg-gray-100">
                      <td className="px-6 py-4 font-medium text-gray-900">InventoryData</td>
                      <td className="px-6 py-4">Current stock levels and reorder points</td>
                      <td className="px-6 py-4 font-mono text-xs">store_id, product_id, stock_on_hand, reorder_point, safety_stock</td>
                    </tr>
                    <tr className="bg-white border-b hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">WeatherData</td>
                      <td className="px-6 py-4">Historical and forecast weather conditions</td>
                      <td className="px-6 py-4 font-mono text-xs">week_end_date, store_id, temperature, precipitation, conditions</td>
                    </tr>
                    <tr className="bg-gray-50 border-b hover:bg-gray-100">
                      <td className="px-6 py-4 font-medium text-gray-900">EventsData</td>
                      <td className="px-6 py-4">Local events affecting demand patterns</td>
                      <td className="px-6 py-4 font-mono text-xs">week_end_date, event, category, store_id, impact_level</td>
                    </tr>
                    <tr className="bg-white border-b hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">ProductHierarchy</td>
                      <td className="px-6 py-4">Product taxonomy and categorization</td>
                      <td className="px-6 py-4 font-mono text-xs">product_id, category, subcategory, brand, description</td>
                    </tr>
                    <tr className="bg-gray-50 border-b hover:bg-gray-100">
                      <td className="px-6 py-4 font-medium text-gray-900">LocationDimension</td>
                      <td className="px-6 py-4">Store locations and regional data</td>
                      <td className="px-6 py-4 font-mono text-xs">store_id, city, state, region, store_type</td>
                    </tr>
                    <tr className="bg-white hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">Calendar</td>
                      <td className="px-6 py-4">Time dimension for analytics</td>
                      <td className="px-6 py-4 font-mono text-xs">date, week_number, month, quarter, year, is_holiday</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Azure AI Search Indexes */}
            <div className="mb-8">
              <h3 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-600" />
                Azure AI Search Indexes
              </h3>
              <div className="overflow-x-auto bg-white border border-gray-200 rounded-lg">
                <table className="min-w-full text-sm text-left text-gray-600">
                  <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 border-b font-semibold">Index Name</th>
                      <th className="px-6 py-3 border-b font-semibold">Purpose</th>
                      <th className="px-6 py-3 border-b font-semibold">Fields</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="bg-white border-b hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">planalytics-products</td>
                      <td className="px-6 py-4">Product entity resolution</td>
                      <td className="px-6 py-4 font-mono text-xs">id, name, category, description, vector_embedding</td>
                    </tr>
                    <tr className="bg-gray-50 border-b hover:bg-gray-100">
                      <td className="px-6 py-4 font-medium text-gray-900">planalytics-locations</td>
                      <td className="px-6 py-4">Location entity resolution</td>
                      <td className="px-6 py-4 font-mono text-xs">id, city, state, region, vector_embedding</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Entity Relationship */}
            <div className="mb-8">
              <h3 className="text-xl font-bold mb-4 text-gray-900">Entity Relationships</h3>
              <div className="bg-gray-900 text-gray-300 p-6 rounded-lg font-mono text-sm overflow-x-auto">
                <pre className="whitespace-pre">{`
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ ProductHierarchy │       │  LocationDimension│       │    Calendar      │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ product_id (PK)  │       │ store_id (PK)    │       │ date (PK)        │
│ category         │       │ city             │       │ week_number      │
│ subcategory      │       │ state            │       │ month            │
│ brand            │       │ region           │       │ quarter          │
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │                          │                          │
         │ (FK)                     │ (FK)                     │ (FK)
         └────────┬─────────────────┴──────────────────────────┘
                  │
         ┌────────▼─────────┐
         │     Metrics      │  ◄─── Main fact table
         ├──────────────────┤
         │ product_id (FK)  │
         │ location_id (FK) │
         │ week_end_date(FK)│
         │ sales_units      │
         │ revenue          │
         └──────────────────┘
                `}</pre>
              </div>
            </div>

            {/* PostgreSQL Query Capabilities */}
            <div>
              <h3 className="text-xl font-bold mb-4 text-gray-900 flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-600" />
                PostgreSQL Query Capabilities
              </h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
                <p className="text-sm text-gray-700 mb-3">
                  Advanced SQL capabilities for complex analytics and time-series analysis.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Query Features:</h4>
                    <ul className="space-y-1 text-gray-700">
                      <li>• Window functions for trends</li>
                      <li>• Aggregations and grouping</li>
                      <li>• Time-series analysis</li>
                      <li>• Complex JOINs across tables</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Performance:</h4>
                    <ul className="space-y-1 text-gray-700">
                      <li>• Indexed columns for fast queries</li>
                      <li>• Materialized views for analytics</li>
                      <li>• Query optimization</li>
                      <li>• Connection pooling</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Agents */}
          <section id="agents" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Cpu className="w-8 h-8 text-[#D04A02]" />
              AI Agents System
            </h2>
            <p className="text-gray-700 mb-6 leading-relaxed">
              The system uses a <strong>multi-agent architecture</strong> powered by <strong>LangGraph</strong> where specialized 
              agents collaborate to handle complex supply chain queries. Each agent is powered by Azure OpenAI GPT-4 and 
              has domain-specific expertise.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              <div className="border-2 border-[#D04A02] rounded-xl p-5 hover:shadow-lg transition-shadow bg-orange-50">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-[#D04A02] text-white p-2 rounded-lg">
                    <Zap className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-900">Orchestrator Agent</h3>
                </div>
                <p className="text-sm text-gray-700 mb-3">The "Brain" that coordinates all other agents using LangGraph state machine.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />
                    Intent classification & routing
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />
                    Agent selection logic
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />
                    Response synthesis
                  </li>
                </ul>
                <div className="mt-3 text-xs font-mono bg-white p-2 rounded border border-orange-200">
                  File: orchestrator_agent.py
                </div>
              </div>

              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow bg-white">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-blue-600 text-white p-2 rounded-lg">
                    <Database className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-900">Database Agent</h3>
                </div>
                <p className="text-sm text-gray-700 mb-3">Converts natural language to SQL queries for data retrieval.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-blue-600" />
                    Dynamic SQL generation
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-blue-600" />
                    Query optimization
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-blue-600" />
                    Result formatting
                  </li>
                </ul>
                <div className="mt-3 text-xs font-mono bg-gray-50 p-2 rounded border border-gray-200">
                  File: database_agent.py
                </div>
              </div>

              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow bg-white">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-green-600 text-white p-2 rounded-lg">
                    <Activity className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-900">Visualization Agent</h3>
                </div>
                <p className="text-sm text-gray-700 mb-3">Generates dynamic chart configurations using LLM analysis.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />
                    Chart type selection
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />
                    Google Charts config
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-green-600" />
                    Smart data mapping
                  </li>
                </ul>
                <div className="mt-3 text-xs font-mono bg-gray-50 p-2 rounded border border-gray-200">
                  File: visualization_agent.py
                </div>
              </div>

              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow bg-white">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-purple-600 text-white p-2 rounded-lg">
                    <Cloud className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-900">Weather Agent</h3>
                </div>
                <p className="text-sm text-gray-700 mb-3">Analyzes weather data and predicts supply chain impacts.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-purple-600" />
                    Temperature analysis
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-purple-600" />
                    Precipitation tracking
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-purple-600" />
                    Impact scoring
                  </li>
                </ul>
                <div className="mt-3 text-xs font-mono bg-gray-50 p-2 rounded border border-gray-200">
                  File: weather_agent.py
                </div>
              </div>

              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow bg-white">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-amber-600 text-white p-2 rounded-lg">
                    <FileText className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-900">Events Agent</h3>
                </div>
                <p className="text-sm text-gray-700 mb-3">Forecasts demand changes based on local events and holidays.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-amber-600" />
                    Event impact analysis
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-amber-600" />
                    Holiday patterns
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-amber-600" />
                    Demand forecasting
                  </li>
                </ul>
                <div className="mt-3 text-xs font-mono bg-gray-50 p-2 rounded border border-gray-200">
                  File: events_agent.py
                </div>
              </div>

              <div className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow bg-white">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-indigo-600 text-white p-2 rounded-lg">
                    <Package className="w-6 h-6" />
                  </div>
                  <h3 className="font-bold text-lg text-gray-900">Inventory Agent</h3>
                </div>
                <p className="text-sm text-gray-700 mb-3">Optimizes inventory levels and prevents stockouts.</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-indigo-600" />
                    Stock level monitoring
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-indigo-600" />
                    Reorder recommendations
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-0.5 text-indigo-600" />
                    Safety stock calculation
                  </li>
                </ul>
                <div className="mt-3 text-xs font-mono bg-gray-50 p-2 rounded border border-gray-200">
                  File: inventory_agent.py
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-300 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4 text-gray-900">Agent Collaboration Workflow</h3>
              <div className="bg-white p-4 rounded border border-gray-200 font-mono text-xs overflow-x-auto">
                <pre>{`
User Query → Orchestrator (LangGraph)
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
  Classify Intent         Extract Context
  (conversation/data/     (location_id,
   visualization)          product_id)
        ↓                       ↓
        └───────────┬───────────┘
                    ↓
            Select Agents
    (based on keywords & intent)
                    ↓
        ┌───────────┴───────────┬───────────┐
        ↓                       ↓           ↓
  Database Agent        Weather Agent  Events Agent
  (SQL + Data)         (Impact Score)  (Forecast)
        ↓                       ↓           ↓
        └───────────┬───────────┴───────────┘
                    ↓
         Visualization Agent
         (Chart Config)
                    ↓
           Synthesize Response
         (Natural Language + Chart)
                    ↓
              Return to User
                `}</pre>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Frontend Structure */}
          <section id="frontend" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Globe className="w-8 h-8 text-[#D04A02]" />
              Frontend Structure
            </h2>
            
            <p className="text-gray-700 mb-6">
              Built with <strong>Next.js 14 App Router</strong> following React best practices and PwC design guidelines.
            </p>

            <div className="bg-gray-50 border border-gray-200 p-6 rounded-xl mb-6">
              <ul className="space-y-2 font-mono text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">📁</span>
                  <div className="flex-1">
                    <strong>frontend/</strong>
                    <ul className="ml-4 mt-2 space-y-1">
                      <li>├── <strong>app/</strong> <span className="text-gray-500">// Next.js App Router pages</span></li>
                      <li className="ml-4">├── page.tsx <span className="text-gray-500">// Main dashboard & chat layout</span></li>
                      <li className="ml-4">├── layout.tsx <span className="text-gray-500">// Root layout with metadata</span></li>
                      <li className="ml-4">├── globals.css <span className="text-gray-500">// Global styles & Tailwind</span></li>
                      <li className="ml-4">└── docs/ <span className="text-gray-500">// This documentation page</span></li>
                      <li>├── <strong>components/</strong> <span className="text-gray-500">// Reusable React components</span></li>
                      <li className="ml-4">├── ChatBox.tsx <span className="text-gray-500">// AI chat interface</span></li>
                      <li className="ml-4">├── GoogleChart.tsx <span className="text-gray-500">// Chart wrapper</span></li>
                      <li className="ml-4">├── Header.tsx <span className="text-gray-500">// App header</span></li>
                      <li className="ml-4">├── StatsPanel.tsx <span className="text-gray-500">// KPI cards</span></li>
                      <li className="ml-4">└── <strong>dashboard/</strong> <span className="text-gray-500">// Dashboard widgets</span></li>
                      <li className="ml-8">├── AdvancedDashboard.tsx <span className="text-gray-500">// Main dashboard container</span></li>
                      <li className="ml-8">├── AnomalyDetector.tsx <span className="text-gray-500">// Real-time anomaly alerts</span></li>
                      <li className="ml-8">├── LiveChart.tsx <span className="text-gray-500">// Auto-updating charts</span></li>
                      <li className="ml-8">├── MetricCard.tsx <span className="text-gray-500">// KPI metric cards</span></li>
                      <li className="ml-8">├── ForecastWidget.tsx <span className="text-gray-500">// Demand forecasting</span></li>
                      <li className="ml-8">├── SmartInsights.tsx <span className="text-gray-500">// AI insights panel</span></li>
                      <li className="ml-8">└── USAWeatherMap.tsx <span className="text-gray-500">// Azure Maps integration</span></li>
                      <li>├── <strong>public/</strong> <span className="text-gray-500">// Static assets</span></li>
                      <li>├── package.json <span className="text-gray-500">// Dependencies</span></li>
                      <li>├── tailwind.config.ts <span className="text-gray-500">// Tailwind + PwC theme</span></li>
                      <li>└── tsconfig.json <span className="text-gray-500">// TypeScript config</span></li>
                    </ul>
                  </div>
                </li>
              </ul>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <h3 className="font-bold text-lg mb-3 text-gray-900">Key Components</h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <Code className="w-4 h-4 mt-0.5 text-[#D04A02]" />
                    <div>
                      <strong>ChatBox.tsx:</strong> Handles user queries, API calls, markdown rendering, and chart display
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <Code className="w-4 h-4 mt-0.5 text-[#D04A02]" />
                    <div>
                      <strong>AdvancedDashboard.tsx:</strong> Role-based views (Store Manager, CFO, Planner, Marketing)
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <Code className="w-4 h-4 mt-0.5 text-[#D04A02]" />
                    <div>
                      <strong>USAWeatherMap.tsx:</strong> Azure Maps with real-time weather overlay
                    </div>
                  </li>
                </ul>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <h3 className="font-bold text-lg mb-3 text-gray-900">Design System</h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div>
                      <strong>PwC Orange:</strong> #D04A02 (primary brand color)
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div>
                      <strong>Typography:</strong> Inter font family
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div>
                      <strong>Icons:</strong> Lucide React (consistent, modern)
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div>
                      <strong>Responsive:</strong> Mobile-first Tailwind CSS
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Backend Structure */}
          <section id="backend" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Server className="w-8 h-8 text-[#D04A02]" />
              Backend Structure
            </h2>

            <div className="bg-gray-50 border border-gray-200 p-6 rounded-xl mb-6">
              <ul className="space-y-2 font-mono text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">📁</span>
                  <div className="flex-1">
                    <strong>backend/</strong>
                    <ul className="ml-4 mt-2 space-y-1">
                      <li>├── main.py <span className="text-gray-500">// FastAPI application entry point</span></li>
                      <li>├── requirements.txt <span className="text-gray-500">// Python dependencies</span></li>
                      <li>├── .env <span className="text-gray-500">// Environment variables (not in git)</span></li>
                      <li>├── <strong>core/</strong> <span className="text-gray-500">// Core utilities</span></li>
                      <li className="ml-4">├── config.py <span className="text-gray-500">// Settings & environment config</span></li>
                      <li className="ml-4">├── logger.py <span className="text-gray-500">// Structured JSON logging</span></li>
                      <li className="ml-4">└── security.py <span className="text-gray-500">// JWT, password hashing</span></li>
                      <li>├── <strong>agents/</strong> <span className="text-gray-500">// AI Agent modules</span></li>
                      <li className="ml-4">├── orchestrator_agent.py <span className="text-gray-500">// Master orchestrator (LangGraph)</span></li>
                      <li className="ml-4">├── database_agent.py <span className="text-gray-500">// SQL generation</span></li>
                      <li className="ml-4">├── visualization_agent.py <span className="text-gray-500">// Chart config generation</span></li>
                      <li className="ml-4">├── weather_agent.py <span className="text-gray-500">// Weather impact analysis</span></li>
                      <li className="ml-4">├── events_agent.py <span className="text-gray-500">// Event forecasting</span></li>
                      <li className="ml-4">├── inventory_agent.py <span className="text-gray-500">// Inventory optimization</span></li>
                      <li className="ml-4">└── location_agent.py <span className="text-gray-500">// Location intelligence</span></li>
                      <li>├── <strong>database/</strong> <span className="text-gray-500">// Database connections</span></li>
                      <li className="ml-4">└── postgres_db.py <span className="text-gray-500">// PostgreSQL ORM models & connection</span></li>
                      <li>├── <strong>routes/</strong> <span className="text-gray-500">// API endpoints</span></li>
                      <li className="ml-4">├── chatbot.py <span className="text-gray-500">// /api/v1/chat endpoints</span></li>
                      <li className="ml-4">├── analytics.py <span className="text-gray-500">// /api/v1/analytics endpoints</span></li>
                      <li className="ml-4">└── reports.py <span className="text-gray-500">// /api/v1/reports endpoints</span></li>
                      <li>└── <strong>services/</strong> <span className="text-gray-500">// Business logic</span></li>
                      <li className="ml-4">├── rag_pipeline.py <span className="text-gray-500">// Context retrieval & SQL generation</span></li>
                      <li className="ml-4">├── data_ingestion.py <span className="text-gray-500">// Data loading utilities</span></li>
                      <li className="ml-4">└── graph_builder.py <span className="text-gray-500">// Data relationship mapping</span></li>
                    </ul>
                  </div>
                </li>
              </ul>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Security */}
          <section id="security" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Shield className="w-8 h-8 text-[#D04A02]" />
              Security & Authentication
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <h3 className="font-bold text-lg mb-3 text-gray-900 flex items-center gap-2">
                  <Lock className="w-5 h-5 text-red-600" />
                  Authentication
                </h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div><strong>JWT Tokens:</strong> python-jose for token generation</div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div><strong>Password Hashing:</strong> bcrypt via passlib</div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div><strong>Token Expiry:</strong> Configurable (default 30min)</div>
                  </li>
                </ul>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <h3 className="font-bold text-lg mb-3 text-gray-900 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-600" />
                  API Security
                </h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div><strong>CORS:</strong> Configured origins for frontend</div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div><strong>GZip Compression:</strong> Response optimization</div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                    <div><strong>Input Validation:</strong> Pydantic models</div>
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-6 h-6 text-amber-600 mt-1" />
                <div>
                  <h3 className="font-bold text-lg mb-2 text-gray-900">Environment Variables Security</h3>
                  <p className="text-sm text-gray-700 mb-3">
                    All sensitive credentials are stored in <code className="bg-white px-2 py-0.5 rounded">.env</code> file 
                    (never committed to git). Use strong <code className="bg-white px-2 py-0.5 rounded">SECRET_KEY</code> in production.
                  </p>
                  <div className="bg-white p-3 rounded border border-amber-200 font-mono text-xs">
                    <div>SECRET_KEY=your-secret-key-here</div>
                    <div>AZURE_OPENAI_API_KEY=your-azure-key</div>
                    <div>POSTGRES_PASSWORD=your-db-password</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Setup Guide */}
          <section id="setup" className="scroll-mt-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
              <Settings className="w-8 h-8 text-[#D04A02]" />
              Setup & Installation Guide
            </h2>

            <div className="space-y-8">
              {/* Prerequisites */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Prerequisites</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Required Software</h4>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Python 3.11+</li>
                      <li>• Node.js 18+</li>
                      <li>• PostgreSQL 14+</li>
                      <li>• Git</li>
                    </ul>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Optional</h4>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Redis (Caching)</li>
                      <li>• Docker</li>
                    </ul>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Azure Services</h4>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Azure OpenAI (Required)</li>
                      <li>• Azure Maps (Optional)</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Backend Setup */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Backend Setup</h3>
                <div className="bg-gray-900 text-gray-100 p-5 rounded-lg">
                  <pre className="text-sm overflow-x-auto">{`# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup environment variables
# Copy .env.example to .env and fill in your credentials
cp .env.example .env

# 6. Initialize database (if needed)
# Run migrations or setup scripts

# 7. Start the server
python main.py

# Server will run at http://localhost:8000`}</pre>
                </div>
              </div>

              {/* Frontend Setup */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Frontend Setup</h3>
                <div className="bg-gray-900 text-gray-100 p-5 rounded-lg">
                  <pre className="text-sm overflow-x-auto">{`# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Setup environment variables
# Create .env file with:
NEXT_PUBLIC_AZURE_MAPS_API_KEY=your-key-here

# 4. Start development server
npm run dev

# Frontend will run at http://localhost:3000

# 5. Build for production
npm run build
npm start`}</pre>
                </div>
              </div>

              {/* Environment Configuration */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Environment Configuration</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
                  <h4 className="font-semibold text-gray-900 mb-3">Backend .env Variables:</h4>
                  <div className="bg-white p-4 rounded border border-blue-200 font-mono text-xs overflow-x-auto">
                    <pre>{`# Application
APP_NAME=Plan IQ
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here

# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=planalytics_db
POSTGRES_PORT=5432

# Azure OpenAI
OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
OPENAI_API_KEY=your-api-key
OPENAI_MODEL_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure Maps (Optional)
AZURE_MAPS_API_KEY=your-maps-key`}</pre>
                  </div>
                </div>
              </div>

              {/* Deployment */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-gray-900">Production Deployment</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-5">
                    <h4 className="font-semibold text-gray-900 mb-3">Backend Deployment</h4>
                    <ul className="text-sm text-gray-700 space-y-2">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Set DEBUG=False
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Use strong SECRET_KEY
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Configure HTTPS
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Use Gunicorn/Uvicorn workers
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Setup reverse proxy (Nginx)
                      </li>
                    </ul>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-5">
                    <h4 className="font-semibold text-gray-900 mb-3">Frontend Deployment</h4>
                    <ul className="text-sm text-gray-700 space-y-2">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Run npm run build
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Deploy to Vercel/Azure
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Configure API URLs
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Enable CDN for static assets
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 text-green-600" />
                        Setup monitoring
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Footer */}
          <div className="mt-20 pt-10 border-t border-gray-200 text-center text-gray-500 text-sm">
            <p>&copy; 2025 Plan IQ - Supply Chain Intelligence Platform. All rights reserved.</p>
            <p className="mt-2">Powered by PwC GenAI</p>
          </div>

        </div>
      </main>
    </div>
  );
}
