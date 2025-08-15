package com.example.fitnessapp.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.fitnessapp.data.ApiService
import com.example.fitnessapp.data.GenerateRecipeResponse
import com.example.fitnessapp.data.RecipeGenerationRequest
import com.example.fitnessapp.utils.formatListString
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun RecipeScreen(userId: Int, onBack: () -> Unit) {
    val api = remember { ApiService.create("https://backend-45111119432.us-central1.run.app/") }
    val prompt = remember { mutableStateOf("") }
    val result = remember { mutableStateOf<GenerateRecipeResponse?>(null) }
    val loading = remember { mutableStateOf(false) }
    val error = remember { mutableStateOf<String?>(null) }

    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())
    ) {
        Text("Recipe Generator", style = MaterialTheme.typography.headlineSmall)
        OutlinedTextField(
            value = prompt.value,
            onValueChange = { prompt.value = it },
            label = { Text("Tell us what you want to eat") },
            modifier = Modifier.fillMaxWidth().padding(top = 12.dp)
        )

        Button(onClick = {
            scope.launch {
                loading.value = true
                error.value = null
                try {
                    val res = withContext(Dispatchers.IO) {
                        api.generateRecipe(RecipeGenerationRequest(userId = userId, userDirections = prompt.value))
                    }
                    result.value = res
                } catch (e: Exception) {
                    error.value = e.message
                } finally {
                    loading.value = false
                }
            }
        }, modifier = Modifier.fillMaxWidth().padding(top = 12.dp), enabled = !loading.value) {
            Text("Generate")
        }

        if (error.value != null) {
            Text(error.value!!, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp))
        }

        result.value?.recipe?.let { r ->
            Card(modifier = Modifier.fillMaxWidth().padding(top = 16.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(r.recipeName, style = MaterialTheme.typography.headlineSmall)
                    
                    if (!r.recipeType.isNullOrBlank()) {
                        Text("Type: ${r.recipeType}", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
                    }
                    
                    if (!r.ingredients.isNullOrBlank()) {
                        Text("Ingredients", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
                        Text(formatListString(r.ingredients), modifier = Modifier.padding(top = 8.dp))
                    }
                    
                    if (!r.instructions.isNullOrBlank()) {
                        Text("Instructions", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
                        Text(formatListString(r.instructions), modifier = Modifier.padding(top = 8.dp))
                    }
                    
                    if (!r.extraCategories.isNullOrBlank()) {
                        Text("Tags", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
                        Text(formatListString(r.extraCategories), modifier = Modifier.padding(top = 8.dp))
                    }
                    
                    Card(
                        modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text("Nutrition", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(bottom = 8.dp))
                            Text("Calories: ${r.calories ?: 0}")
                            Text("Protein: ${r.protein ?: 0.0}g")
                            Text("Carbs: ${r.carbs ?: 0.0}g")
                            Text("Fat: ${r.fat ?: 0.0}g")
                        }
                    }
                }
            }
        }

        Button(onClick = onBack, modifier = Modifier.fillMaxWidth().padding(top = 16.dp)) { Text("Back") }
    }
}

