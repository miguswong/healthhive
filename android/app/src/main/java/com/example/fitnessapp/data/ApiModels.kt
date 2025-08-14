package com.example.fitnessapp.data

import com.squareup.moshi.Json

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val success: Boolean,
    val message: String,
    val user: UserSummary?
)

data class UserSummary(
    val id: Int,
    val name: String,
    val email: String,
    @Json(name = "weight_goal") val weightGoal: String?
)

data class User(
    val id: Int,
    val name: String,
    val email: String,
    @Json(name = "weight_goal") val weightGoal: String?,
    val password: String?
)

data class Activity(
    @Json(name = "activity_id") val activityId: Int?,
    @Json(name = "user_id") val userId: Int,
    @Json(name = "activity_type") val activityType: String,
    val distance: Double?,
    @Json(name = "distance_units") val distanceUnits: String?,
    val time: Double?,
    @Json(name = "time_units") val timeUnits: String?,
    val speed: Double?,
    @Json(name = "speed_units") val speedUnits: String?,
    @Json(name = "calories_burned") val caloriesBurned: Int?,
    @Json(name = "activity_date") val activityDate: String
)

data class LatestWeight(
    val weight: Double?,
    @Json(name = "weight_units") val weightUnits: String?,
    @Json(name = "weight_kg") val weightKg: Double?,
    val date: String?,
    val notes: String?,
    val found: Boolean
)

data class RecipeGenerationRequest(
    @Json(name = "user_id") val userId: Int,
    @Json(name = "user_directions") val userDirections: String,
    val model: String? = null
)

data class Recipe(
    @Json(name = "recipe_id") val recipeId: Int?,
    @Json(name = "recipe_name") val recipeName: String,
    @Json(name = "recipe_type") val recipeType: String?,
    @Json(name = "recipe_source") val recipeSource: String?,
    @Json(name = "source_user_id") val sourceUserId: Int?,
    @Json(name = "recipe_url") val recipeUrl: String?,
    val ingredients: String?,
    val instructions: String?,
    val directions: String?,
    val calories: Int?,
    val fat: Double?,
    val carbs: Double?,
    val protein: Double?,
    @Json(name = "extra_categories") val extraCategories: String?
)

data class GenerateRecipeResponse(
    val success: Boolean,
    val message: String?,
    val recipe: Recipe?
)

