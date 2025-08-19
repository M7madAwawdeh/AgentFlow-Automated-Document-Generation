<x-app-layout>
    <x-slot name="header">
        <div class="flex justify-between items-center">
            <h2 class="font-semibold text-xl text-gray-800 leading-tight">
                🤖 AgentFlow Dashboard
            </h2>
            <a href="{{ route('ai.projects.create') }}" 
               class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200">
                + New Project
            </a>
        </div>
    </x-slot>

    <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            
            <!-- Statistics Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                    <div class="p-6">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <svg class="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                                </svg>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-gray-500">Total Projects</p>
                                <p class="text-2xl font-semibold text-gray-900">{{ $stats['total_projects'] }}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                    <div class="p-6">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-gray-500">Completed Sessions</p>
                                <p class="text-2xl font-semibold text-gray-900">{{ $stats['completed_sessions'] }}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                    <div class="p-6">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <svg class="h-8 w-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-gray-500">Total Sessions</p>
                                <p class="text-2xl font-semibold text-gray-900">{{ $stats['total_sessions'] }}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                    <div class="p-6">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <svg class="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                                </svg>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-gray-500">Failed Sessions</p>
                                <p class="text-2xl font-semibold text-gray-900">{{ $stats['failed_sessions'] }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Welcome Section -->
            <div class="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg mb-8">
                <div class="px-6 py-8 text-white">
                    <h1 class="text-3xl font-bold mb-4">Welcome to AgentFlow! 🚀</h1>
                    <p class="text-xl mb-6">
                        Your AI-powered development team that automatically generates documentation, tests, security reports, and performance optimizations.
                    </p>
                    <div class="flex flex-wrap gap-4">
                        <a href="{{ route('ai.projects.create') }}" 
                           class="bg-white text-blue-600 hover:bg-gray-100 font-bold py-3 px-6 rounded-lg transition duration-200">
                            Start Your First Project
                        </a>
                        <a href="#how-it-works" 
                           class="border-2 border-white text-white hover:bg-white hover:text-blue-600 font-bold py-3 px-6 rounded-lg transition duration-200">
                            Learn How It Works
                        </a>
                    </div>
                </div>
            </div>

            <!-- Recent Analysis Sessions -->
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg mb-8">
                <div class="p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Recent Analysis Sessions</h3>
                    
                    @if($recentSessions->count() > 0)
                        <div class="space-y-4">
                            @foreach($recentSessions as $session)
                                <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition duration-200">
                                    <div class="flex justify-between items-start">
                                        <div class="flex-1">
                                            <h4 class="font-medium text-gray-900">
                                                <a href="{{ route('ai.sessions.show', $session->session_uuid) }}" 
                                                   class="hover:text-blue-600">
                                                    {{ $session->project->name }} - Session #{{ substr($session->session_uuid, 0, 8) }}
                                                </a>
                                            </h4>
                                            <p class="text-sm text-gray-600 mt-1">
                                                Started {{ $session->started_at->diffForHumans() }}
                                            </p>
                                            <div class="flex items-center mt-2">
                                                @php
                                                    $statusColors = [
                                                        'started' => 'bg-blue-100 text-blue-800',
                                                        'in_progress' => 'bg-yellow-100 text-yellow-800',
                                                        'completed' => 'bg-green-100 text-green-800',
                                                        'failed' => 'bg-red-100 text-red-800'
                                                    ];
                                                    $statusColor = $statusColors[$session->status] ?? 'bg-gray-100 text-gray-800';
                                                @endphp
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ $statusColor }}">
                                                    {{ ucfirst(str_replace('_', ' ', $session->status)) }}
                                                </span>
                                            </div>
                                        </div>
                                        <div class="text-right">
                                            <a href="{{ route('ai.sessions.show', $session->session_uuid) }}" 
                                               class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                                                View Details →
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            @endforeach
                        </div>
                        
                        <div class="mt-6 text-center">
                            <a href="#" class="text-blue-600 hover:text-blue-800 font-medium">
                                View All Sessions →
                            </a>
                        </div>
                    @else
                        <div class="text-center py-8">
                            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                            </svg>
                            <h3 class="mt-2 text-sm font-medium text-gray-900">No analysis sessions yet</h3>
                            <p class="mt-1 text-sm text-gray-500">Get started by creating your first project.</p>
                            <div class="mt-6">
                                <a href="{{ route('ai.projects.create') }}" 
                                   class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                                    Create Project
                                </a>
                            </div>
                        </div>
                    @endif
                </div>
            </div>

            <!-- Projects Overview -->
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg mb-8">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Your Projects</h3>
                        <a href="{{ route('ai.projects.create') }}" 
                           class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            + Add Project
                        </a>
                    </div>
                    
                    @if($projects->count() > 0)
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            @foreach($projects as $project)
                                <div class="border border-gray-200 rounded-lg p-6 hover:shadow-md transition duration-200">
                                    <div class="flex justify-between items-start mb-4">
                                        <h4 class="font-medium text-gray-900">{{ $project->name }}</h4>
                                        @php
                                            $statusColors = [
                                                'pending' => 'bg-gray-100 text-gray-800',
                                                'analyzing' => 'bg-yellow-100 text-yellow-800',
                                                'completed' => 'bg-green-100 text-green-800',
                                                'failed' => 'bg-red-100 text-red-800'
                                            ];
                                            $statusColor = $statusColors[$project->status] ?? 'bg-gray-100 text-gray-800';
                                        @endphp
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ $statusColor }}">
                                            {{ ucfirst($project->status) }}
                                        </span>
                                    </div>
                                    
                                    @if($project->description)
                                        <p class="text-sm text-gray-600 mb-4">{{ Str::limit($project->description, 100) }}</p>
                                    @endif
                                    
                                    <div class="space-y-2 mb-4">
                                        @if($project->git_repository)
                                            <div class="flex items-center text-sm text-gray-500">
                                                <svg class="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm0 2h12v8H4V6z" clip-rule="evenodd"></path>
                                                </svg>
                                                {{ Str::limit($project->git_repository, 30) }}
                                            </div>
                                        @endif
                                        
                                        <div class="flex items-center text-sm text-gray-500">
                                            <svg class="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
                                            </svg>
                                            {{ $project->created_at->diffForHumans() }}
                                        </div>
                                    </div>
                                    
                                    <div class="flex space-x-2">
                                        <a href="{{ route('ai.projects.show', $project->id) }}" 
                                           class="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-center py-2 px-4 rounded text-sm font-medium transition duration-200">
                                            View Project
                                        </a>
                                        <a href="{{ route('ai.projects.upload', $project->id) }}" 
                                           class="flex-1 bg-green-600 hover:bg-green-700 text-white text-center py-2 px-4 rounded text-sm font-medium transition duration-200">
                                            Upload Files
                                        </a>
                                    </div>
                                </div>
                            @endforeach
                        </div>
                        
                        <div class="mt-6">
                            {{ $projects->links() }}
                        </div>
                    @else
                        <div class="text-center py-8">
                            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                            </svg>
                            <h3 class="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
                            <p class="mt-1 text-sm text-gray-500">Create your first project to get started with AI analysis.</p>
                            <div class="mt-6">
                                <a href="{{ route('ai.projects.create') }}" 
                                   class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                                    Create Project
                                </a>
                            </div>
                        </div>
                    @endif
                </div>
            </div>

            <!-- How It Works Section -->
            <div id="how-it-works" class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                <div class="p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-6">How AgentFlow Works</h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div class="text-center">
                            <div class="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                                <span class="text-2xl font-bold text-blue-600">1</span>
                            </div>
                            <h4 class="font-medium text-gray-900 mb-2">Upload Your Code</h4>
                            <p class="text-sm text-gray-600">Upload PHP files, JavaScript, Vue components, or connect via Git repository.</p>
                        </div>
                        
                        <div class="text-center">
                            <div class="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                                <span class="text-2xl font-bold text-blue-600">2</span>
                            </div>
                            <h4 class="font-medium text-gray-900 mb-2">AI Agents Analyze</h4>
                            <p class="text-sm text-gray-600">Our AI team analyzes your code for documentation, testing, security, and performance.</p>
                        </div>
                        
                        <div class="text-center">
                            <div class="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                                <span class="text-2xl font-bold text-blue-600">3</span>
                            </div>
                            <h4 class="font-medium text-gray-900 mb-2">Get Comprehensive Reports</h4>
                            <p class="text-sm text-gray-600">Receive detailed reports with actionable insights and generated code.</p>
                        </div>
                        
                        <div class="text-center">
                            <div class="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                                <span class="text-2xl font-bold text-blue-600">4</span>
                            </div>
                            <h4 class="font-medium text-gray-900 mb-2">Apply & Improve</h4>
                            <p class="text-sm text-gray-600">One-click apply generated tests, documentation, and optimizations to your codebase.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    @push('scripts')
    <script>
        // Auto-refresh dashboard every 30 seconds
        setInterval(function() {
            location.reload();
        }, 30000);
    </script>
    @endpush
</x-app-layout>
