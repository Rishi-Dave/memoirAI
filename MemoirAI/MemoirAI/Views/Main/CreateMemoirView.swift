import SwiftUI

struct CreateMemoirView: View {
    @StateObject private var viewModel = CreateMemoirViewModel()
    @State private var showImagePicker = false
    @State private var showCamera = false
    @State private var userContext = ""
    @State private var selectedTone: MemoirTone = .heartwarming
    
    let onMemoirCreated: ((String) -> Void)?
        
    // Add initializer
    init(onMemoirCreated: ((String) -> Void)? = nil) {
        self.onMemoirCreated = onMemoirCreated
    }

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Instructions
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Create Your Memoir")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Add photos and let AI create a beautiful story from your memories.")
                            .foregroundColor(.secondary)
                    }
                    
                    // Photo selection
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Photos")
                            .font(.headline)
                        
                        if viewModel.selectedImages.isEmpty {
                            // Empty state
                            VStack(spacing: 16) {
                                Image(systemName: "photo.badge.plus")
                                    .font(.system(size: 40))
                                    .foregroundColor(.gray)
                                
                                Text("Add photos to get started")
                                    .foregroundColor(.secondary)
                                
                                HStack(spacing: 16) {
                                    Button("Camera") {
                                        showCamera = true
                                    }
                                    .buttonStyle(.bordered)
                                    
                                    Button("Photo Library") {
                                        showImagePicker = true
                                    }
                                    .buttonStyle(.bordered)
                                }
                            }
                            .frame(height: 200)
                            .frame(maxWidth: .infinity)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(12)
                        } else {
                            // Selected images
                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible())
                            ], spacing: 8) {
                                ForEach(viewModel.selectedImages.indices, id: \.self) { index in
                                    ZStack(alignment: .topTrailing) {
                                        Image(uiImage: viewModel.selectedImages[index])
                                            .resizable()
                                            .aspectRatio(contentMode: .fill)
                                            .frame(height: 100)
                                            .clipped()
                                            .cornerRadius(8)
                                        
                                        Button(action: {
                                            viewModel.selectedImages.remove(at: index)
                                        }) {
                                            Image(systemName: "xmark.circle.fill")
                                                .foregroundColor(.white)
                                                .background(Color.black.opacity(0.6))
                                                .clipShape(Circle())
                                        }
                                        .padding(4)
                                    }
                                }
                                
                                // Add more button
                                if viewModel.selectedImages.count < 6 {
                                    Button(action: {
                                        showImagePicker = true
                                    }) {
                                        VStack {
                                            Image(systemName: "plus")
                                                .font(.title2)
                                            Text("Add More")
                                                .font(.caption)
                                        }
                                        .frame(height: 100)
                                        .frame(maxWidth: .infinity)
                                        .background(Color.gray.opacity(0.2))
                                        .cornerRadius(8)
                                    }
                                }
                            }
                        }
                    }
                    
                    // User context
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Context (Optional)")
                            .font(.headline)
                        
                        TextField("Tell us more about these photos...", text: $userContext, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(3...6)
                    }
                    
                    // Tone selection
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Story Tone")
                            .font(.headline)
                        
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack {
                                ForEach(MemoirTone.allCases, id: \.self) { tone in
                                    Button(tone.rawValue.capitalized) {
                                        selectedTone = tone
                                    }
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 8)
                                    .background(selectedTone == tone ? Color.blue : Color.gray.opacity(0.2))
                                    .foregroundColor(selectedTone == tone ? .white : .primary)
                                    .cornerRadius(20)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                    
                    // Create button
                    Button(action: createMemoir) {
                        HStack {
                            if viewModel.isCreating {
                                ProgressView()
                                    .scaleEffect(0.8)
                            }
                            Text(viewModel.isCreating ? "Creating Your Story..." : "Create Memoir")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(viewModel.selectedImages.isEmpty ? Color.gray : Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .disabled(viewModel.selectedImages.isEmpty || viewModel.isCreating)
                }
                .padding()
            }
            .navigationTitle("")
            .navigationBarHidden(true)
            .sheet(isPresented: $showImagePicker) {
                ImagePicker(selectedImages: $viewModel.selectedImages, allowsMultipleSelection: true)
            }
            .sheet(isPresented: $showCamera) {
                CameraPicker(selectedImage: .constant(nil)) { image in
                    if let image = image {
                        viewModel.selectedImages.append(image)
                    }
                }
            }
            .alert("Success!", isPresented: $viewModel.showSuccess) {
                Button("View Memoir") {
                    if let entry = viewModel.createdEntry {
                        print("📖 Created memoir: \(entry.title)")
                        // Navigate to home and show this memoir
                        onMemoirCreated?(entry.entryId)
                    }
                    viewModel.resetForm()
                }
                Button("Create Another") {
                    viewModel.resetForm()
                }
            } message: {
                if let entry = viewModel.createdEntry {
                    Text("Your memoir '\(entry.title)' has been created successfully!")
                } else {
                    Text("Your memoir has been created successfully!")
                }
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK") { }
                Button("Debug Info") {
                    print("🐛 Debug - Error details: \(viewModel.errorMessage)")
                }
            } message: {
                Text(viewModel.errorMessage)
            }
        }
    }
    
    private func createMemoir() {
        Task {
            await viewModel.createMemoir(
                images: viewModel.selectedImages,
                userContext: userContext,
                tone: selectedTone
            )
        }
    }
}

#Preview {
    CreateMemoirView()
}
