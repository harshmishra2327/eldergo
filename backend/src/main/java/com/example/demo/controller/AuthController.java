package com.example.demo.controller;

import com.example.demo.dto.LoginRequest;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @PostMapping(value = "/register", consumes = "multipart/form-data")
    public String register(
            @RequestParam String role,
            @RequestParam String username,
            @RequestParam String password,
            @RequestParam("full_name") String fullName,
            @RequestParam String phone,
            @RequestParam String email,
            @RequestParam Integer age,
            @RequestParam String gender,
            @RequestParam String address,
            @RequestParam(required = false) String emergency_contact,
            @RequestParam(required = false) String medical_notes,
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String pincode,
            @RequestParam(required = false) String languages,
            @RequestParam(required = false) String availability,
            @RequestParam(required = false) String preferred_service,
            @RequestParam(required = false) String other_service_details,
            @RequestParam(required = false) String skills,
            @RequestParam(required = false) String experience
    ) {

        System.out.println("===== REGISTRATION REQUEST =====");

        System.out.println("Role: " + role);
        System.out.println("Username: " + username);
        System.out.println("Full Name: " + fullName);
        System.out.println("Email: " + email);
        System.out.println("Phone: " + phone);
        System.out.println("Age: " + age);
        System.out.println("Gender: " + gender);
        System.out.println("Address: " + address);

        if ("client".equals(role)) {
            System.out.println("Emergency Contact: " + emergency_contact);
            System.out.println("Medical Notes: " + medical_notes);
        }

        if ("companion".equals(role)) {
            System.out.println("City: " + city);
            System.out.println("Pincode: " + pincode);
            System.out.println("Languages: " + languages);
            System.out.println("Availability: " + availability);
            System.out.println("Preferred Service: " + preferred_service);
            System.out.println("Other Service: " + other_service_details);
            System.out.println("Skills: " + skills);
            System.out.println("Experience: " + experience);
        }

        return "Registration request received successfully!";
    }

    @PostMapping("/login")
    public String login(@RequestBody LoginRequest request) {

        System.out.println("===== LOGIN REQUEST =====");
        System.out.println("Username: " + request.getUsername());
        System.out.println("Password: " + request.getPassword());

        if ("admin".equals(request.getUsername())
                && "admin123".equals(request.getPassword())) {

            return "Login successful! Role: admin";
        }

        if ("client".equals(request.getUsername())
                && "client123".equals(request.getPassword())) {

            return "Login successful! Role: client";
        }

        if ("companion".equals(request.getUsername())
                && "companion123".equals(request.getPassword())) {

            return "Login successful! Role: companion";
        }

        return "Invalid username or password";
    }
}
