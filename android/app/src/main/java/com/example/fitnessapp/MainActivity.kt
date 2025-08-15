package com.example.fitnessapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.fitnessapp.ui.screens.DataScreen
import com.example.fitnessapp.ui.screens.LoginScreen
import com.example.fitnessapp.ui.screens.RecipeScreen
import com.example.fitnessapp.ui.screens.RecipesListScreen
import com.example.fitnessapp.ui.screens.RecipeDetailScreen
import com.example.fitnessapp.ui.screens.BiometricsScreen
import com.example.fitnessapp.ui.theme.FitnessTheme
import com.example.fitnessapp.data.Recipe
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import java.net.URLEncoder
import java.net.URLDecoder

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            FitnessTheme {
                Surface(color = MaterialTheme.colorScheme.background) {
                    AppNavHost()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppNavHost(modifier: Modifier = Modifier, navController: NavHostController = rememberNavController()) {
    val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
    val recipeAdapter = moshi.adapter(Recipe::class.java)
    
    NavHost(navController = navController, startDestination = "login", modifier = modifier) {
        composable("login") {
            LoginScreen(onLoginSuccess = { userId ->
                navController.navigate("data/$userId") {
                    popUpTo("login") { inclusive = true }
                }
            })
        }
        composable("data/{userId}") { backStackEntry ->
            val userId = backStackEntry.arguments?.getString("userId")?.toIntOrNull() ?: 0
            DataScreen(
                userId = userId,
                onGenerateRecipe = { navController.navigate("recipes/$userId") },
                onBrowseRecipes = { navController.navigate("recipesList") },
                onViewBiometrics = { navController.navigate("biometrics/$userId") }
            )
        }
        composable("recipes/{userId}") { backStackEntry ->
            val userId = backStackEntry.arguments?.getString("userId")?.toIntOrNull() ?: 0
            RecipeScreen(userId = userId, onBack = { navController.popBackStack() })
        }
        composable("biometrics/{userId}") { backStackEntry ->
            val userId = backStackEntry.arguments?.getString("userId")?.toIntOrNull() ?: 0
            BiometricsScreen(userId = userId, onBack = { navController.popBackStack() })
        }
        composable("recipesList") {
            RecipesListScreen(
                onBack = { navController.popBackStack() },
                onRecipeClick = { recipe ->
                    try {
                        val recipeJson = recipeAdapter.toJson(recipe)
                        val encodedRecipe = URLEncoder.encode(recipeJson, "UTF-8")
                        navController.navigate("recipeDetail/$encodedRecipe")
                    } catch (e: Exception) {
                        // Fallback to simple navigation if serialization fails
                        navController.navigate("recipeDetail/fallback")
                    }
                }
            )
        }
        composable("recipeDetail/{recipeJson}") { backStackEntry ->
            val encodedRecipe = backStackEntry.arguments?.getString("recipeJson") ?: ""
            val recipe = try {
                val recipeJson = URLDecoder.decode(encodedRecipe, "UTF-8")
                recipeAdapter.fromJson(recipeJson) ?: Recipe(
                    recipeId = 1,
                    recipeName = "Error loading recipe",
                    recipeType = null,
                    recipeSource = null,
                    sourceUserId = null,
                    recipeUrl = null,
                    ingredients = null,
                    instructions = null,
                    directions = null,
                    calories = null,
                    fat = null,
                    carbs = null,
                    protein = null,
                    extraCategories = null
                )
            } catch (e: Exception) {
                Recipe(
                    recipeId = 1,
                    recipeName = "Error loading recipe",
                    recipeType = null,
                    recipeSource = null,
                    sourceUserId = null,
                    recipeUrl = null,
                    ingredients = null,
                    instructions = null,
                    directions = null,
                    calories = null,
                    fat = null,
                    carbs = null,
                    protein = null,
                    extraCategories = null
                )
            }
            RecipeDetailScreen(recipe = recipe, onBack = { navController.popBackStack() })
        }
    }
}

