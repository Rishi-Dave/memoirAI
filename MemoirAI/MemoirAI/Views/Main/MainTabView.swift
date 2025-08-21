//
//  MainTabView.swift
//  MemoirAI
//
//  Created by Rishi Dave on 8/20/25.
//

import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    @State private var selectedEntryId: String?
    
    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView(selectedEntryId: $selectedEntryId)
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("Home")
                }
                .tag(0)
            
            CreateMemoirView(
                onMemoirCreated: { entryId in
                    // Navigate to home and show the created memoir
                    selectedEntryId = entryId
                    selectedTab = 0
                }
            )
                .tabItem {
                    Image(systemName: "plus.circle.fill")
                    Text("Create")
                }
                .tag(1)
            
            FavoritesView()
                .tabItem {
                    Image(systemName: "heart.fill")
                    Text("Favorites")
                }
                .tag(2)
            
            ProfileView()
                .tabItem {
                    Image(systemName: "person.fill")
                    Text("Profile")
                }
                .tag(3)
        }
        .accentColor(.blue)
    }
}
