package com.example.fitnessapp.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import com.example.fitnessapp.data.ApiService
import com.example.fitnessapp.data.Recipe
import com.example.fitnessapp.utils.formatListString
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import android.content.Intent
import android.net.Uri

@Composable
fun RecipesListScreen(onBack: () -> Unit, onRecipeClick: (Recipe) -> Unit) {
    val api = remember { ApiService.create("https://backend-45111119432.us-central1.run.app/") }
    val scope = rememberCoroutineScope()

    val recipeType = remember { mutableStateOf("") }
    val extraCategories = remember { mutableStateOf("") }
    val recipes = remember { mutableStateListOf<Recipe>() }
    val loading = remember { mutableStateOf(false) }
    val error = remember { mutableStateOf<String?>(null) }

    fun fetch() {
        scope.launch {
            loading.value = true
            error.value = null
            try {
                val list = withContext(Dispatchers.IO) {
                    api.getRecipes(
                        recipeType = recipeType.value.ifBlank { null },
                        extraCategories = extraCategories.value.ifBlank { null }
                    )
                }
                recipes.clear()
                recipes.addAll(list)
            } catch (e: Exception) {
                error.value = "Failed to load recipes: ${e.message}"
            } finally {
                loading.value = false
            }
        }
    }

    LaunchedEffect(Unit) { fetch() }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Browse Recipes", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        
        // Filter controls
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = recipeType.value,
                onValueChange = { recipeType.value = it },
                label = { Text("Type (e.g., Vegan, Keto)") },
                modifier = Modifier.weight(1f)
            )
            OutlinedTextField(
                value = extraCategories.value,
                onValueChange = { extraCategories.value = it },
                label = { Text("Category tag") },
                modifier = Modifier.weight(1f)
            )
        }
        
        Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { fetch() }, enabled = !loading.value) { Text("Filter") }
            Button(onClick = {
                recipeType.value = ""
                extraCategories.value = ""
                fetch()
            }) { Text("Clear") }
            Button(onClick = onBack) { Text("Back") }
        }
        
        if (error.value != null) {
            Text(error.value!!, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp))
        }

        Spacer(Modifier.height(16.dp))

        // Recipe count
        Text("${recipes.size} recipes found", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(bottom = 8.dp))

        if (loading.value) {
            Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (recipes.isEmpty()) {
            Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                Text("No recipes found", style = MaterialTheme.typography.bodyLarge)
            }
        } else {
            LazyColumn {
                items(recipes) { recipe ->
                    RecipeCard(recipe = recipe, onClick = { onRecipeClick(recipe) })
                }
            }
        }
    }
}

@Composable
fun RecipeCard(recipe: Recipe, onClick: () -> Unit) {
    val context = LocalContext.current
    
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable { onClick() },
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(
                    recipe.recipeName,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f)
                )
                if (!recipe.recipeType.isNullOrBlank()) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
                    ) {
                        Text(
                            recipe.recipeType,
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }
                }
            }
            
            if (!recipe.extraCategories.isNullOrBlank()) {
                Text(
                    formatListString(recipe.extraCategories),
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(top = 4.dp)
                )
            }
            
            // Display recipe URL if available
            if (!recipe.recipeUrl.isNullOrBlank()) {
                Text(
                    "View Recipe",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary,
                    textDecoration = TextDecoration.Underline,
                    modifier = Modifier
                        .padding(top = 8.dp)
                        .clickable {
                            try {
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(recipe.recipeUrl))
                                context.startActivity(intent)
                            } catch (e: Exception) {
                                // Handle invalid URL
                            }
                        }
                )
            }
            
            Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Calories: ${recipe.calories ?: 0}", style = MaterialTheme.typography.bodySmall)
                Text("Protein: ${recipe.protein ?: 0.0}g", style = MaterialTheme.typography.bodySmall)
                Text("Carbs: ${recipe.carbs ?: 0.0}g", style = MaterialTheme.typography.bodySmall)
                Text("Fat: ${recipe.fat ?: 0.0}g", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
fun RecipeDetailScreen(recipe: Recipe, onBack: () -> Unit) {
    val context = LocalContext.current
    
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())
    ) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Recipe Details", style = MaterialTheme.typography.headlineSmall)
            Button(onClick = onBack) { Text("Back") }
        }
        
        Spacer(Modifier.height(16.dp))
        
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(recipe.recipeName, style = MaterialTheme.typography.headlineSmall)
                
                if (!recipe.recipeType.isNullOrBlank()) {
                    Text("Type: ${recipe.recipeType}", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
                }
                
                // Display recipe URL if available
                if (!recipe.recipeUrl.isNullOrBlank()) {
                    Text(
                        "View Original Recipe",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                        textDecoration = TextDecoration.Underline,
                        modifier = Modifier
                            .padding(top = 8.dp)
                            .clickable {
                                try {
                                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(recipe.recipeUrl))
                                    context.startActivity(intent)
                                } catch (e: Exception) {
                                    // Handle invalid URL
                                }
                            }
                    )
                }
                
                if (!recipe.ingredients.isNullOrBlank()) {
                    Text("Ingredients", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
                    Text(formatListString(recipe.ingredients), modifier = Modifier.padding(top = 8.dp))
                }
                
                if (!recipe.instructions.isNullOrBlank()) {
                    Text("Instructions", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
                    Text(formatListString(recipe.instructions), modifier = Modifier.padding(top = 8.dp))
                }
                
                if (!recipe.extraCategories.isNullOrBlank()) {
                    Text("Tags", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
                    Text(formatListString(recipe.extraCategories), modifier = Modifier.padding(top = 8.dp))
                }
                
                Card(
                    modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Nutrition", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(bottom = 8.dp))
                        Text("Calories: ${recipe.calories ?: 0}")
                        Text("Protein: ${recipe.protein ?: 0.0}g")
                        Text("Carbs: ${recipe.carbs ?: 0.0}g")
                        Text("Fat: ${recipe.fat ?: 0.0}g")
                    }
                }
            }
        }
    }
}

