//
//  HomeView.swift
//  MemoirAI
//
//  Created by Rishi Dave on 8/20/25.
//

import SwiftUI

struct HomeView: View {
    @StateObject private var viewModel = HomeViewModel()
    @Binding var selectedEntryId: String?
    
    init(selectedEntryId: Binding<String?> = .constant(nil)) {
        self._selectedEntryId = selectedEntryId
    }
    
    var body: some View {
        NavigationView {
            Group {
                if viewModel.isLoading {
                    LoadingView(message: "Loading your memoirs...")
                } else if viewModel.entries.isEmpty {
                    VStack(spacing: 20) {
                        Image(systemName: "book.pages")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        
                        Text("No Memoirs Yet")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("Create your first memoir by adding photos in the Create tab.")
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                } else {
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            ForEach(viewModel.entries) { entry in
                                EntryCardView(entry: entry)
                                    .onTapGesture {
                                        viewModel.selectedEntry = entry
                                    }
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("My Memoirs")
            .refreshable {
                await viewModel.loadEntries()
            }
            .task {
                await viewModel.loadEntries()
            }
            .sheet(item: $viewModel.selectedEntry) { entry in
                EntryDetailView(entry: entry)
            }
            .onChange(of: selectedEntryId) { entryId in
                // When a specific entry is selected, refresh data and show it
                if let entryId = entryId {
                    Task {
                        await viewModel.refreshAndShowEntry(entryId: entryId)
                        // Clear the selection after handling
                        selectedEntryId = nil
                    }
                }
            }
        }
    }
}
