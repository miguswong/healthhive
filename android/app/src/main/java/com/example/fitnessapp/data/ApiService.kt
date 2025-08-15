package com.example.fitnessapp.data

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import java.util.concurrent.TimeUnit

interface ApiService {
    @POST("login")
    suspend fun login(@Body body: LoginRequest): LoginResponse

    @GET("users/{id}")
    suspend fun getUser(@Path("id") id: Int): User

    @GET("users/{id}/latest-weight")
    suspend fun getLatestWeight(@Path("id") id: Int): LatestWeight

    @GET("activities")
    suspend fun getActivities(@Query("user_id") userId: Int): List<Activity>

    @GET("biometrics")
    suspend fun getBiometrics(@Query("user_id") userId: Int): List<Biometrics>

    @POST("biometrics")
    suspend fun createBiometric(@Body body: Biometrics): Biometrics

    @POST("generate-recipe")
    suspend fun generateRecipe(@Body body: RecipeGenerationRequest): GenerateRecipeResponse

    @GET("recipes")
    suspend fun getRecipes(
        @Query("recipe_type") recipeType: String? = null,
        @Query("extra_categories") extraCategories: String? = null
    ): List<Recipe>

    companion object {
        fun create(baseUrl: String): ApiService {
            val logging = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
            val client = OkHttpClient.Builder()
                .addInterceptor(logging)
                .connectTimeout(60, TimeUnit.SECONDS)
                .readTimeout(90, TimeUnit.SECONDS)
                .writeTimeout(90, TimeUnit.SECONDS)
                .retryOnConnectionFailure(true)
                .build()

            val moshi = Moshi.Builder()
                .add(KotlinJsonAdapterFactory())
                .build()

            return Retrofit.Builder()
                .baseUrl(baseUrl)
                .addConverterFactory(MoshiConverterFactory.create(moshi))
                .client(client)
                .build()
                .create(ApiService::class.java)
        }
    }
}

