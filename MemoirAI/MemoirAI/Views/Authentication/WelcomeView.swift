import SwiftUI

struct WelcomeView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var isSignUp = false
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            // App Logo & Title
            VStack(spacing: 16) {
                Image(systemName: "book.pages.fill")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)
                
                Text("MemoirAI")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Turn your photos into beautiful stories")
                    .font(.title3)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            Spacer()
            
            // Auth Form
            VStack(spacing: 20) {
                // Toggle between Sign In / Sign Up
                Picker("Auth Mode", selection: $isSignUp) {
                    Text("Sign In").tag(false)
                    Text("Sign Up").tag(true)
                }
                .pickerStyle(SegmentedPickerStyle())
                
                // Email field
                TextField("Email", text: $email)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)
                
                // Password field
                SecureField("Password", text: $password)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .textContentType(.none)  // Disable autofill suggestions
                    .autocorrectionDisabled(true)  // Disable autocorrection
                
                // Confirm password (only for sign up)
                if isSignUp {
                    SecureField("Confirm Password", text: $confirmPassword)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .textContentType(.none)  // Disable autofill suggestions
                        .autocorrectionDisabled(true)  // Disable autocorrection
                }
                
                // Submit button
                Button(action: submitForm) {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .scaleEffect(0.8)
                        }
                        Text(isLoading ? "Please wait..." : (isSignUp ? "Create Account" : "Sign In"))
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isFormValid ? Color.blue : Color.gray)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(!isFormValid || isLoading)
                
                // Password requirements (for sign up)
                if isSignUp {
                    Text("Password must be at least 6 characters")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
        }
        .padding()
        .alert("Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .onChange(of: isSignUp) { _ in
            clearForm()
        }
    }
    
    private var isFormValid: Bool {
        let emailValid = email.contains("@") && email.contains(".")
        let passwordValid = password.count >= 6
        
        if isSignUp {
            return emailValid && passwordValid && password == confirmPassword
        } else {
            return emailValid && !password.isEmpty
        }
    }
    
    private func submitForm() {
        isLoading = true
        
        Task {
            do {
                if isSignUp {
                    try await authManager.signUp(email: email, password: password)
                } else {
                    try await authManager.signIn(email: email, password: password)
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    showError = true
                    isLoading = false
                }
            }
        }
    }
    
    private func clearForm() {
        password = ""
        confirmPassword = ""
        errorMessage = ""
    }
}

#Preview {
    WelcomeView()
        .environmentObject(AuthenticationManager())
}
